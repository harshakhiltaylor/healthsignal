"""
Re-embed all existing trials with the new enriched chunk format.
Run this once after upgrading the embedding pipeline.

Usage:
    source venv2/bin/activate
    python re_embed_all.py
"""
import asyncio
import logging
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import Trial
from agents.embed import run_embed

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def build_trial_text(trial: Trial) -> str:
    """Build the same enriched text as the new _embed_node."""
    parts = []
    if trial.title:
        parts.append(f"Title: {trial.title}")
    if trial.condition:
        parts.append(f"Condition: {trial.condition}")
    if trial.phase:
        parts.append(f"Phase: {trial.phase}")
    if trial.sponsor:
        parts.append(f"Sponsor: {trial.sponsor}")
    if trial.intervention:
        parts.append(f"Interventions: {trial.intervention}")
    if trial.start_date:
        parts.append(f"Start Date: {trial.start_date}")
    if trial.completion_date:
        parts.append(f"Completion Date: {trial.completion_date}")
    if trial.enrollment:
        parts.append(f"Enrollment: {trial.enrollment} participants")
    if trial.extracted_drugs:
        parts.append(f"Drugs: {', '.join(trial.extracted_drugs)}")
    if trial.extracted_conditions:
        parts.append(f"Conditions (NER): {', '.join(trial.extracted_conditions)}")
    if trial.ai_summary:
        parts.append(f"Summary: {trial.ai_summary}")
    elif trial.brief_summary:
        parts.append(f"Summary: {trial.brief_summary}")
    return "\n".join(parts)


async def re_embed_all(batch_size: int = 50):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Trial.id))
        all_ids = [r[0] for r in result.fetchall()]

    total = len(all_ids)
    logger.info(f"Re-embedding {total} trials...")

    success = 0
    failed = 0

    for i in range(0, total, batch_size):
        batch_ids = all_ids[i:i + batch_size]
        async with AsyncSessionLocal() as db:
            for trial_id in batch_ids:
                trial = await db.get(Trial, trial_id)
                if not trial:
                    continue
                try:
                    text = await build_trial_text(trial)
                    if text.strip():
                        await run_embed(trial_id=trial_id, text=text)
                        success += 1
                except Exception as e:
                    logger.warning(f"Failed to re-embed {trial_id}: {e}")
                    failed += 1

        pct = min(100, int((i + batch_size) / total * 100))
        logger.info(f"Progress: {min(i + batch_size, total)}/{total} ({pct}%) | OK={success} FAIL={failed}")

    logger.info(f"Re-embed complete. Success={success}, Failed={failed}")


if __name__ == "__main__":
    asyncio.run(re_embed_all())
