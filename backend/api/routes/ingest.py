"""Ingest status and manual trigger endpoints."""
import logging
from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import select
from db.models import IngestLog
from models.schemas import IngestStatusOut

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/ingest/logs")
async def ingest_logs(limit: int = 20):
    """Return ingest logs; gracefully returns empty list if DB is unreachable."""
    try:
        from db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(IngestLog).order_by(IngestLog.run_at.desc()).limit(limit)
            )
            rows = result.scalars().all()
            return [IngestStatusOut.model_validate(r) for r in rows]
    except Exception as e:
        logger.warning(f"Could not fetch ingest logs (DB may be down): {e}")
        return []


def _run_ingest_sync(query: str, log_id: int | None = None):
    """Run ingest in a background thread (fallback when Celery is unavailable)."""
    from pipeline._ingest_runner import ingest_all
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(ingest_all(query=query, log_id=log_id))
    except Exception as e:
        logger.error(f"Background ingest failed: {e}")
    finally:
        loop.close()


@router.post("/ingest/trigger")
async def trigger_ingest(background_tasks: BackgroundTasks, query: str = ""):
    """Manually trigger an ingestion run. Tries Celery first, falls back to background thread."""
    from db.session import AsyncSessionLocal
    from db.models import IngestLog

    log_id = None
    try:
        async with AsyncSessionLocal() as db:
            log = IngestLog(status="queued")
            db.add(log)
            await db.commit()
            log_id = log.id
    except Exception as e:
        logger.error(f"Failed to create IngestLog before queueing: {e}")

    try:
        from pipeline.tasks import run_nightly_ingest
        result = run_nightly_ingest.delay(query=query, log_id=log_id)
        return {"status": "queued", "message": f"Ingest task queued via Celery (task_id={result.id})"}
    except Exception as e:
        logger.warning(f"Celery unavailable ({e}), running ingest in background thread")
        background_tasks.add_task(_run_ingest_sync, query, log_id)
        return {"status": "queued", "message": "Celery unavailable — running ingest directly in background"}
