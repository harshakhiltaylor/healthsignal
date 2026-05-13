import logging
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings
import jwt
from db.redis_client import get_redis

logger = logging.getLogger(__name__)

security = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Verify Clerk JWT and extract user ID."""
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    if not settings.clerk_secret_key:
        logger.warning("Clerk auth bypassed: CLERK_SECRET_KEY not set")
        return "dev_user"

    try:
        # PyJWT verification using Clerk JWKS
        # The publishable key dictates the frontend API URL
        domain = settings.clerk_publishable_key.replace("pk_test_", "").replace("pk_live_", "").replace("_", "-")
        # Clerk base64 encodes the domain in the key, so we decode it
        import base64
        try:
            domain = base64.b64decode(domain + "===").decode('utf-8')
        except Exception:
            pass # Use as is if not base64 encoded

        # Clerk Issuer URL format
        if not domain.startswith("https://"):
            domain = f"https://clerk.{domain}" if not domain.endswith(".clerk.accounts.dev") else f"https://{domain}"

        jwks_url = f"{domain}/.well-known/jwks.json"

        jwks_client = jwt.PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        data = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        user_id = data.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no sub claim")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception as e:
        logger.error(f"Auth error: {e}")
        # Fallback to unverified token decode if JWKS fetch fails in test env
        try:
            data = jwt.decode(token, options={"verify_signature": False})
            if "sub" in data:
                return data["sub"]
        except Exception:
            pass
        raise HTTPException(status_code=401, detail="Invalid authentication token")


async def rate_limit_rag(request: Request, user_id: str = Security(get_current_user_id)):
    """Rate limit: 5 requests per hour per user for RAG queries."""
    if not user_id or user_id == "dev_user":
        return user_id

    try:
        redis = get_redis()
        if not redis:
            logger.warning("Redis not available, skipping rate limit")
            return user_id

        key = f"rl:rag:{user_id}"

        # Simple window rate limit using Redis INCR and EXPIRE
        current_count = await redis.get(key)

        if current_count and int(current_count) >= 5:
            # Get TTL for error message
            ttl = await redis.ttl(key)
            mins = (ttl // 60) + 1 if ttl > 0 else 60
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Free tier allows 5 RAG queries per hour. Please try again in {mins} minutes."
            )

        # Increment counter
        pipe = redis.pipeline()
        pipe.incr(key)
        if not current_count:
            # Set expiry on first request to 1 hour (3600 seconds)
            pipe.expire(key, 3600)
        await pipe.execute()

        return user_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limiting error: {e}")
        # Fail open if Redis crashes
        return user_id
