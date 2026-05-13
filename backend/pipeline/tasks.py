"""
Celery tasks — called by beat scheduler or triggered manually.
"""
import asyncio
import logging
import time
from celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="pipeline.tasks.run_nightly_ingest", bind=True, max_retries=2)
def run_nightly_ingest(self, query: str = "", max_pages: int | None = None, log_id: int | None = None):
    """
    Nightly ingestion task.
    Fetches new/updated trials from ClinicalTrials.gov,
    runs the full agent DAG, and writes to PGVector.
    """
    from pipeline._ingest_runner import ingest_all
    logger.info("Starting nightly ingest run")
    start = time.time()
    try:
        result = _run_async(ingest_all(query=query, max_pages=max_pages, log_id=log_id))
        logger.info(f"Ingest complete in {time.time()-start:.1f}s: {result}")
        return result
    except Exception as exc:
        retries = self.request.retries
        backoff = 60 * (2 ** retries)  # 60s, 120s, 240s...
        logger.error(f"Ingest failed (retry {retries}/{self.max_retries}): {exc}")
        raise self.retry(exc=exc, countdown=backoff)


@celery_app.task(name="pipeline.tasks.run_nightly_eval")
def run_nightly_eval():
    """
    Nightly RAGAS eval run on a held-out question set.
    Writes scores to eval_results table.
    Logs a warning if faithfulness drops below threshold.
    """
    from eval.ragas_eval import run_eval_suite
    logger.info("Starting nightly eval run")
    result = _run_async(run_eval_suite())
    logger.info(f"Eval complete: {result}")
    return result


@celery_app.task(name="pipeline.tasks.process_single_trial")
def process_single_trial(trial_dict: dict):
    """
    Process a single trial through the agent DAG.
    Used for on-demand processing and testing.
    """
    from agents.router import run_agent_dag
    logger.info(f"Processing trial {trial_dict.get('id')}")
    result = _run_async(run_agent_dag(trial_dict))
    return {"trial_id": trial_dict.get("id"), "status": "processed"}
