"""
Full ingest run — fetches, deduplicates, and processes trials.
"""
import logging
import time
import httpx
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import Trial, IngestLog
from pipeline.ingest import fetch_trials, fetch_trial_results
from pipeline.dedup import is_duplicate, needs_update
from agents.router import run_agent_dag

logger = logging.getLogger(__name__)


async def ingest_all(query: str = "", max_pages: int | None = None, log_id: int | None = None) -> dict:
    start = time.time()
    stats = {"fetched": 0, "new": 0, "updated": 0, "skipped": 0, "errors": 0}

    async with AsyncSessionLocal() as db, httpx.AsyncClient() as http_client:
        # Load existing IDs into memory for fast dedup
        result = await db.execute(select(Trial.id))
        existing_ids: set[str] = set(r[0] for r in result.fetchall())

        # Get or create the ingest log entry
        log = None
        if log_id:
            log = await db.get(IngestLog, log_id)

        if log:
            log.status = "running"
        else:
            log = IngestLog(status="running")
            db.add(log)

        await db.commit()

        async for trial_data in fetch_trials(query=query, max_pages=max_pages):
            stats["fetched"] += 1
            trial_id = trial_data.get("id", "")

            if not trial_id:
                stats["errors"] += 1
                continue

            try:
                modified = False
                if await is_duplicate(trial_data, existing_ids):
                    existing = await db.get(Trial, trial_id)
                    if not needs_update(trial_data, existing):
                        stats["skipped"] += 1
                    else:
                        # Update existing trial
                        for k, v in trial_data.items():
                            if hasattr(existing, k):
                                setattr(existing, k, v)
                        existing.processed = False
                        stats["updated"] += 1
                        modified = True
                else:
                    # New trial
                    trial_obj = Trial(**{
                        k: v for k, v in trial_data.items()
                        if k in Trial.__table__.columns.keys()
                    })
                    db.add(trial_obj)
                    existing_ids.add(trial_id)
                    stats["new"] += 1
                    modified = True

                # Live-update log in DB
                log.trials_fetched = stats["fetched"]
                log.trials_new = stats["new"]
                log.trials_updated = stats["updated"]
                log.trials_skipped = stats["skipped"]
                log.errors = stats["errors"]

                if modified or stats["fetched"] % 10 == 0:
                    await db.commit()

                if modified:
                    # For completed trials, enrich with outcome results data
                    status = trial_data.get("status", "")
                    if status == "COMPLETED":
                        results_text = await fetch_trial_results(trial_id, http_client)
                        if results_text:
                            existing_summary = trial_data.get("brief_summary", "") or ""
                            trial_data["brief_summary"] = (
                                existing_summary + "\n\nOutcome Results: " + results_text
                            )

                    # Run full agent DAG (NER → ZSC → Summary → Embed → Persist)
                    try:
                        await run_agent_dag(trial_data)
                    except Exception as e:
                        logger.warning(f"Agent DAG failed for {trial_id}: {e}")
                        stats["errors"] += 1
                        log.errors = stats["errors"]
                        await db.commit()

            except Exception as e:
                logger.error(f"Failed to process {trial_id}: {e}")
                stats["errors"] += 1
                await db.rollback()
                db.add(log)

        # Final log update
        log.trials_fetched = stats["fetched"]
        log.trials_new = stats["new"]
        log.trials_updated = stats["updated"]
        log.trials_skipped = stats["skipped"]
        log.errors = stats["errors"]
        log.duration_seconds = time.time() - start
        log.status = "complete"
        await db.commit()

    logger.info(f"Ingest run complete: {stats}")
    return stats
