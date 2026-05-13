"""Eval results endpoint."""
import logging
from fastapi import APIRouter, Query
from sqlalchemy import select, func
from db.session import AsyncSessionLocal
from db.models import EvalResult
from models.schemas import EvalResultOut, EvalSummary
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/evals")
async def list_evals(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
):
    """Return eval results; gracefully returns empty list if DB is unreachable."""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(EvalResult).order_by(EvalResult.created_at.desc()).limit(limit).offset(offset)
            )
            rows = result.scalars().all()
            return [EvalResultOut.model_validate(r) for r in rows]
    except Exception as e:
        logger.warning(f"Could not fetch eval results (DB may be down): {e}")
        return []


@router.get("/evals/summary")
async def eval_summary():
    """Return eval summary; returns zeroed summary if DB is unreachable."""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(
                    func.avg(EvalResult.faithfulness),
                    func.avg(EvalResult.answer_relevance),
                    func.avg(EvalResult.context_recall),
                    func.avg(EvalResult.judge_score),
                    func.count(EvalResult.id),
                )
            )
            row = result.one()

            below = await db.execute(
                select(func.count(EvalResult.id)).where(
                    EvalResult.faithfulness < settings.ragas_faithfulness_threshold
                )
            )

            return EvalSummary(
                avg_faithfulness=round(float(row[0] or 0), 3),
                avg_answer_relevance=round(float(row[1] or 0), 3),
                avg_context_recall=round(float(row[2] or 0), 3),
                avg_judge_score=round(float(row[3] or 0), 3),
                total_evals=int(row[4] or 0),
                below_threshold=int(below.scalar() or 0),
                threshold=settings.ragas_faithfulness_threshold,
            )
    except Exception as e:
        logger.warning(f"Could not fetch eval summary (DB may be down): {e}")
        return EvalSummary(
            avg_faithfulness=0,
            avg_answer_relevance=0,
            avg_context_recall=0,
            avg_judge_score=0,
            total_evals=0,
            below_threshold=0,
            threshold=settings.ragas_faithfulness_threshold,
        )
