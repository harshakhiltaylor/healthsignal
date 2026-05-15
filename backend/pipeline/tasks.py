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
    _run_async(run_agent_dag(trial_dict))
    return {"trial_id": trial_dict.get("id"), "status": "processed"}


@celery_app.task(name="pipeline.tasks.re_embed_all_trials")
def re_embed_all_trials():
    """
    Re-embed ALL trials already in the database, bypassing fetch/dedup.
    Useful when the embedding model changes or embeddings are missing/corrupt.
    """
    async def _re_embed():
        from db.session import AsyncSessionLocal
        from db.models import Trial, TrialChunk
        from agents.router import run_agent_dag
        from sqlalchemy import select

        # Fetch only the IDs first to save memory and avoid asyncpg timeouts
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Trial.id).outerjoin(TrialChunk).where(TrialChunk.id == None)
            )
            trial_ids = result.scalars().all()

        logger.info(f"Re-embedding {len(trial_ids)} trials from database...")
        success, failed = 0, 0

        for t_id in trial_ids:
            try:
                # Fetch full trial one by one in a short-lived session
                async with AsyncSessionLocal() as db:
                    trial = await db.get(Trial, t_id)
                
                if not trial:
                    continue

                trial_dict = {
                    "id": trial.id,
                    "title": trial.title or "",
                    "condition": trial.condition or "",
                    "intervention": trial.intervention or "",
                    "brief_summary": trial.brief_summary or "",
                    "phase": trial.phase,
                    "sponsor": trial.sponsor,
                    "start_date": trial.start_date,
                    "completion_date": trial.completion_date,
                    "enrollment": trial.enrollment,
                }
                await run_agent_dag(trial_dict)
                success += 1
                if success % 10 == 0:
                    logger.info(f"Re-embed progress: {success}/{len(trial_ids)} done")
            except Exception as e:
                logger.error(f"Re-embed failed for {t_id}: {e}")
                failed += 1

        logger.info(f"Re-embed complete: {success} succeeded, {failed} failed")
        return {"success": success, "failed": failed, "total": len(trial_ids)}

    return _run_async(_re_embed())


@celery_app.task(name="pipeline.tasks.generate_newsletter")
def generate_newsletter():
    """
    Detect top 5 trending clinical trial topics from the DB
    and generate AI-written articles using Groq. Cache in newsletter_cache.
    Falls back to last 7 days if no data found in last 24h.
    """
    async def _generate():
        import os
        import httpx
        import json as _json
        from db.session import AsyncSessionLocal
        from db.models import NewsletterCache
        from sqlalchemy import text

        # ── Step 1: Read rows in a short-lived session, then close it ──
        rows = []
        async with AsyncSessionLocal() as db:
            for window in ["24 hours", "7 days", "30 days"]:
                result = await db.execute(text(f"""
                    SELECT condition, therapeutic_area, COUNT(*) as cnt
                    FROM trials
                    WHERE condition IS NOT NULL
                    AND created_at >= NOW() - INTERVAL '{window}'
                    GROUP BY condition, therapeutic_area
                    ORDER BY cnt DESC
                    LIMIT 5
                """))
                rows = result.fetchall()
                if rows:
                    logger.info(f"Found {len(rows)} trending topics in last {window}")
                    break

            if not rows:
                result = await db.execute(text("""
                    SELECT condition, therapeutic_area, COUNT(*) as cnt
                    FROM trials
                    WHERE condition IS NOT NULL
                    GROUP BY condition, therapeutic_area
                    ORDER BY cnt DESC
                    LIMIT 5
                """))
                rows = result.fetchall()
        # DB session is now fully closed before we hit Groq

        # ── Step 2: Call Groq for each topic (no DB session open) ──
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        topics = []

        async with httpx.AsyncClient(timeout=30) as http:
            for rank, row in enumerate(rows, start=1):
                condition = row[0] or "Unknown"
                therapeutic_area = row[1] or "General Medicine"
                trial_count = int(row[2])

                prompt = f"""You are a medical journalist writing for a clinical research newsletter.

Write a short, engaging article about the clinical trial topic: "{condition}" (therapeutic area: {therapeutic_area}).

There are currently {trial_count} active clinical trials studying this condition.

Respond in this exact JSON format, no markdown, no code blocks:
{{
  "headline": "A punchy, 10-15 word headline about this topic's latest developments",
  "teaser": "One sentence (max 20 words) summarising why this is trending now.",
  "body": "Three paragraphs of plain-English clinical insight. Paragraph 1: what the condition is and why it matters. Paragraph 2: what current trials are exploring. Paragraph 3: what the future looks like for patients and researchers."
}}"""

                try:
                    resp = await http.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {groq_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "llama3-8b-8192",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.7,
                            "max_tokens": 500,
                        },
                    )
                    resp.raise_for_status()
                    content = resp.json()["choices"][0]["message"]["content"].strip()
                    article = _json.loads(content)
                except Exception as e:
                    logger.warning(f"Groq generation failed for {condition}: {e}")
                    article = {
                        "headline": f"Spotlight: {condition} Clinical Trials",
                        "teaser": f"Researchers are actively studying {condition} across {trial_count} ongoing trials.",
                        "body": (
                            f"Clinical research into {condition} continues to grow. With {trial_count} trials "
                            f"currently registered, this area represents an active frontier in medical research.\n\n"
                            f"Trials across multiple phases are investigating a range of therapeutic approaches. "
                            f"From early-stage safety studies to large Phase 3 efficacy trials, the research "
                            f"landscape is diverse and rapidly evolving.\n\n"
                            f"For patients and clinicians alike, the expanding evidence base offers new hope. "
                            f"As results emerge, they will shape treatment guidelines and open doors to better, "
                            f"more personalised care."
                        ),
                    }

                topics.append({
                    "rank": rank,
                    "condition": condition,
                    "therapeutic_area": therapeutic_area,
                    "trial_count": trial_count,
                    "headline": article.get("headline", f"Trending: {condition}"),
                    "teaser": article.get("teaser", ""),
                    "body": article.get("body", ""),
                })

        # ── Step 3: Write to DB in a fresh session ──
        async with AsyncSessionLocal() as db:
            cache_entry = NewsletterCache(topics=topics)
            db.add(cache_entry)
            await db.commit()

        logger.info(f"Newsletter cache updated with {len(topics)} topics")
        return {"topics_generated": len(topics)}

    return _run_async(_generate())

