"""
RAG Q&A endpoint — retrieves relevant chunks, generates grounded answer,
scores with judge agent, writes eval result to DB.
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db.session import get_db
from db.models import EvalResult
from models.schemas import RAGRequest, RAGResponse, TrialBase
from agents.embed import _embed_text
from agents.judge import rag_query, run_judge
from api.auth import rate_limit_rag

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/rag", response_model=RAGResponse)
async def rag_answer(req: RAGRequest, db: AsyncSession = Depends(get_db), user_id: str = Depends(rate_limit_rag)):
    # 1. Embed question
    query_vec = await _embed_text(req.question)
    if query_vec is None:
        return RAGResponse(
            question=req.question,
            answer="Unable to embed query.",
            sources=[],
        )

    # 2. Retrieve top-k chunks (no processed filter — search all trials)
    sql = text("""
        SELECT tc.chunk_text, tc.trial_id,
               t.title, t.status, t.phase, t.sponsor,
               t.condition, t.therapeutic_area,
               t.start_date, t.completion_date, t.enrollment,
               1 - (tc.embedding <=> CAST(:qv AS vector)) as score
        FROM trial_chunks tc
        JOIN trials t ON tc.trial_id = t.id
        ORDER BY tc.embedding <=> CAST(:qv AS vector)
        LIMIT :top_k
    """)
    result = await db.execute(sql, {"qv": str(query_vec), "top_k": max(req.top_k, 10)})
    rows = result.fetchall()

    if not rows:
        return RAGResponse(
            question=req.question,
            answer="No relevant trials found.",
            sources=[],
        )

    # Build rich context: prefix each chunk with its trial metadata
    enriched_chunks = []
    for row in rows:
        meta = (
            f"[Trial ID: {row.trial_id} | Title: {row.title} | "
            f"Phase: {row.phase} | Status: {row.status} | "
            f"Sponsor: {row.sponsor} | Condition: {row.condition}]\n"
            f"{row.chunk_text}"
        )
        enriched_chunks.append(meta)

    context = "\n\n---\n\n".join(enriched_chunks)

    # 3. Generate answer with Groq using enriched chunks
    answer = await rag_query(req.question, enriched_chunks)

    # 4. Score with judge agent using same enriched context
    judge_scores = await run_judge(req.question, context, answer)

    # 5. Write eval result
    eval_result = EvalResult(
        query=req.question,
        answer=answer,
        context=context[:5000],
        judge_score=judge_scores.get("overall"),
        faithfulness=judge_scores.get("faithfulness"),
        answer_relevance=judge_scores.get("relevance"),
        judge_reasoning=judge_scores.get("reasoning"),
        eval_type="judge",
    )
    db.add(eval_result)
    await db.commit()
    await db.refresh(eval_result)

    # 6. Build source list (deduplicated by trial)
    seen = set()
    sources = []
    for row in rows:
        if row.trial_id not in seen:
            seen.add(row.trial_id)
            sources.append(TrialBase(
                id=row.trial_id,
                title=row.title,
                status=row.status,
                phase=row.phase,
                sponsor=row.sponsor,
                condition=row.condition,
                therapeutic_area=row.therapeutic_area,
                start_date=row.start_date,
                completion_date=row.completion_date,
                enrollment=row.enrollment,
            ))

    return RAGResponse(
        question=req.question,
        answer=answer,
        sources=sources,
        faithfulness_score=judge_scores.get("faithfulness"),
        eval_id=eval_result.id,
    )
