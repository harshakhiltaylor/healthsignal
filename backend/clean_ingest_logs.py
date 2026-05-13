import asyncio
from sqlalchemy import update
from db.session import AsyncSessionLocal
from db.models import IngestLog

async def main():
    async with AsyncSessionLocal() as session:
        # Update all running ingests to failed since they are stuck
        stmt = (
            update(IngestLog)
            .where(IngestLog.status == "running")
            .values(status="failed", error_detail="Marked as failed due to being stuck in running state.")
        )
        result = await session.execute(stmt)
        await session.commit()
        print(f"Updated {result.rowcount} stuck ingest runs to 'failed'.")

if __name__ == "__main__":
    asyncio.run(main())
