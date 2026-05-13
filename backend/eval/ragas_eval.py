"""
RAGAS evaluation pipeline.
Scores the RAG system on a held-out question set.
Writes results to eval_results table.
Logs a warning if faithfulness drops below threshold.
Free: RAGAS is fully open source.
"""
import logging
import json
from pathlib import Path
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from db.session import AsyncSessionLocal
from db.models import EvalResult
from config import settings

logger = logging.getLogger(__name__)

# Held-out eval questions — extend this with real domain questions
EVAL_QUESTIONS_PATH = Path(__file__).parent / "eval_questions.json"

FALLBACK_QUESTIONS = [
    {
        "question": "What Phase 2 trials are studying GLP-1 receptor agonists for obesity?",
        "ground_truth": "Phase 2 clinical trials investigating GLP-1 receptor agonists for obesity treatment.",
    },
    {
        "question": "Which oncology trials are currently recruiting for lung cancer?",
        "ground_truth": "Active recruiting trials in oncology for lung cancer treatment.",
    },
    {
        "question": "What are recent immunotherapy trials for melanoma?",
        "ground_truth": "Clinical trials using immunotherapy approaches for melanoma.",
    },
    {
        "question": "Are there any pediatric trials for rare metabolic diseases?",
        "ground_truth": "Pediatric clinical trials targeting rare metabolic conditions.",
    },
    {
        "question": "What CNS trials are in Phase 3 for Alzheimer's disease?",
        "ground_truth": "Phase 3 clinical trials for Alzheimer's disease treatment.",
    },
]


def _load_eval_questions() -> list[dict]:
    if EVAL_QUESTIONS_PATH.exists():
        with open(EVAL_QUESTIONS_PATH) as f:
            return json.load(f)
    return FALLBACK_QUESTIONS


async def run_eval_suite() -> dict:
    """
    Run full RAGAS eval on held-out question set.
    Writes per-question results to DB.
    Returns aggregate scores.
    """
    from agents.embed import _embed_text
    from agents.judge import rag_query
    from sqlalchemy import text

    questions = _load_eval_questions()[: settings.eval_sample_size]
    logger.info(f"Running eval on {len(questions)} questions")

    eval_rows = []

    async with AsyncSessionLocal() as db:
        for item in questions:
            question = item["question"]
            ground_truth = item.get("ground_truth", "")

            # Retrieve context
            query_vec = await _embed_text(question)
            if query_vec is None:
                continue

            result = await db.execute(
                text("""
                    SELECT tc.chunk_text FROM trial_chunks tc
                    JOIN trials t ON tc.trial_id = t.id
                    WHERE t.processed = true
                    ORDER BY tc.embedding <=> :qv::vector
                    LIMIT 5
                """),
                {"qv": str(query_vec)},
            )
            chunks = [row[0] for row in result.fetchall()]

            if not chunks:
                continue

            # Generate answer
            answer = await rag_query(question, chunks)
            context_str = "\n\n".join(chunks)

            eval_rows.append({
                "question": question,
                "answer": answer,
                "contexts": chunks,
                "ground_truth": ground_truth,
                "context_str": context_str,
            })

    if not eval_rows:
        logger.warning("No eval rows generated — is the DB populated?")
        return {"error": "no_data"}

    # Run RAGAS
    try:
        dataset = Dataset.from_list([
            {
                "question": r["question"],
                "answer": r["answer"],
                "contexts": r["contexts"],
                "ground_truth": r["ground_truth"],
            }
            for r in eval_rows
        ])

        scores = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_recall],
        )
        scores_df = scores.to_pandas()

    except Exception as e:
        logger.error(f"RAGAS eval failed: {e}")
        scores_df = None

    # Persist results
    async with AsyncSessionLocal() as db:
        for i, row in enumerate(eval_rows):
            faith = float(scores_df["faithfulness"].iloc[i]) if scores_df is not None else None
            relevance = float(scores_df["answer_relevancy"].iloc[i]) if scores_df is not None else None
            recall = float(scores_df["context_recall"].iloc[i]) if scores_df is not None else None

            db.add(EvalResult(
                query=row["question"],
                answer=row["answer"],
                context=row["context_str"][:5000],
                faithfulness=faith,
                answer_relevance=relevance,
                context_recall=recall,
                eval_type="ragas",
            ))
        await db.commit()

    if scores_df is not None:
        agg = {
            "avg_faithfulness": round(float(scores_df["faithfulness"].mean()), 3),
            "avg_answer_relevancy": round(float(scores_df["answer_relevancy"].mean()), 3),
            "avg_context_recall": round(float(scores_df["context_recall"].mean()), 3),
            "n": len(eval_rows),
        }
        if agg["avg_faithfulness"] < settings.ragas_faithfulness_threshold:
            logger.warning(
                f"FAITHFULNESS BELOW THRESHOLD: {agg['avg_faithfulness']:.3f} "
                f"< {settings.ragas_faithfulness_threshold}"
            )
        logger.info(f"Eval results: {agg}")
        return agg

    return {"n": len(eval_rows), "error": "ragas_failed"}
