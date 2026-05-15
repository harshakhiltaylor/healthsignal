"""
Newsletter API routes.
GET  /api/newsletter         — Returns the latest cached newsletter (public).
POST /api/newsletter/refresh — Triggers regeneration via Celery (admin).
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter
from db.session import AsyncSessionLocal
from db.models import NewsletterCache
from sqlalchemy import select, desc

logger = logging.getLogger(__name__)
router = APIRouter()

CACHE_TTL_HOURS = 24


@router.get("/newsletter")
async def get_newsletter():
    """Return the latest cached newsletter. Regenerates if stale or missing."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(NewsletterCache).order_by(desc(NewsletterCache.generated_at)).limit(1)
        )
        latest = result.scalar_one_or_none()

        # If no cache or older than 24h, trigger fresh generation synchronously
        is_stale = (
            latest is None
            or latest.generated_at < datetime.utcnow() - timedelta(hours=CACHE_TTL_HOURS)
        )

        if is_stale:
            logger.info("Newsletter cache stale or missing — generating fresh newsletter")
            try:
                from pipeline.tasks import generate_newsletter
                generate_newsletter.delay()
            except Exception as e:
                logger.warning(f"Could not queue newsletter generation: {e}")

        if latest is None:
            return {"generated_at": None, "topics": [], "status": "generating"}

        return {
            "generated_at": latest.generated_at.isoformat(),
            "topics": latest.topics,
            "status": "fresh" if not is_stale else "refreshing",
        }


@router.post("/newsletter/refresh")
async def refresh_newsletter():
    """Admin endpoint — force-regenerate the newsletter immediately."""
    try:
        from pipeline.tasks import generate_newsletter
        result = generate_newsletter.delay()
        return {"status": "queued", "task_id": result.id}
    except Exception as e:
        logger.error(f"Failed to queue newsletter generation: {e}")
        return {"status": "error", "message": str(e)}
