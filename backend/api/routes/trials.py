from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.session import get_db
from db.models import Trial
from models.schemas import TrialDetail

router = APIRouter()

@router.get("/trials")
async def get_trials(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    phase: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    # Build filter conditions
    conditions = []
    if phase:
        conditions.append(Trial.phase.ilike(f"%{phase}%"))
    if status:
        conditions.append(Trial.status == status)

    # Get total count
    count_stmt = select(func.count()).select_from(Trial)
    if conditions:
        count_stmt = count_stmt.where(*conditions)
    total = await db.scalar(count_stmt)

    # Get trials
    stmt = select(Trial)
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.order_by(Trial.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(stmt)
    trials = result.scalars().all()

    return {
        "total": total,
        "items": [TrialDetail.model_validate(t) for t in trials],
        "skip": skip,
        "limit": limit
    }
