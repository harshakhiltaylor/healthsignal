import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from config import settings

async def test():
    engine = create_async_engine(settings.database_url, connect_args={"prepared_statement_cache_size": 0, "statement_cache_size": 0})
    try:
        async with engine.begin() as conn:
            import sqlalchemy as sa
            result = await conn.execute(sa.text("SELECT COUNT(*) FROM trials"))
            count = result.scalar()
            print(f"Total trials in DB: {count}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
