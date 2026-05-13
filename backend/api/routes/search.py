"""
Search endpoint — hybrid semantic search using PGVector.
Supports metadata filters: phase, status, therapeutic_area.
"""
import logging
import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from prometheus_client import Histogram
from db.session import get_db
from db.models import Trial, TrialChunk
from models.schemas import SearchRequest, SearchResponse, SearchResult, TrialBase
from agents.embed import _embed_text
from api.auth import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

SEARCH_LATENCY = Histogram("healthsignal_search_latency_seconds", "Search latency")


@router.post("/search", response_model=SearchResponse)
async def semantic_search(req: SearchRequest, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    start = time.time()

    # Embed the query using same model as documents
    query_embedding = await _embed_text(req.query)
    if query_embedding is None:
        return SearchResponse(query=req.query, results=[], total=0)

    # Build filter clause
    filters = []
    params: dict = {"query_vec": str(query_embedding), "top_k": req.top_k}

    if req.phase_filter:
        filters.append("t.phase ILIKE :phase")
        params["phase"] = f"%{req.phase_filter}%"
    if req.status_filter:
        filters.append("t.status = :status")
        params["status"] = req.status_filter
    if req.therapeutic_area_filter:
        filters.append("t.therapeutic_area = :ta")
        params["ta"] = req.therapeutic_area_filter

    where_clause = ("AND " + " AND ".join(filters)) if filters else ""

    sql = text(f"""
        SELECT
            tc.id as chunk_id,
            tc.trial_id,
            tc.chunk_text,
            1 - (tc.embedding <=> CAST(:query_vec AS vector)) as score,
            t.title, t.status, t.phase, t.sponsor,
            t.condition, t.therapeutic_area,
            t.start_date, t.completion_date, t.enrollment
        FROM trial_chunks tc
        JOIN trials t ON tc.trial_id = t.id
        WHERE t.processed = true
        {where_clause}
        ORDER BY tc.embedding <=> CAST(:query_vec AS vector)
        LIMIT :top_k
    """)

    result = await db.execute(sql, params)
    rows = result.fetchall()

    results = []
    for rank, row in enumerate(rows, start=1):
        trial = TrialBase(
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
        )
        results.append(SearchResult(
            trial=trial,
            score=round(float(row.score), 4),
            chunk_text=row.chunk_text,
            rank=rank,
        ))

    latency = time.time() - start
    SEARCH_LATENCY.observe(latency)
    logger.info(f"Search '{req.query[:50]}' → {len(results)} results in {latency:.3f}s")

    return SearchResponse(query=req.query, results=results, total=len(results))
