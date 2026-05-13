import redis.asyncio as redis
import logging
from config import settings

logger = logging.getLogger(__name__)

_redis_client = None

def get_redis() -> redis.Redis:
    """Get the async Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        try:
            # We use Upstash rediss:// URL
            _redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                ssl_cert_reqs=None if "upstash" in settings.redis_url else "required"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
    return _redis_client
