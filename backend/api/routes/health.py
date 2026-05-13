"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db.session import get_db

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "healthsignal-api"}


@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
