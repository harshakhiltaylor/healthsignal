import asyncio
import sqlalchemy as org_sqlalchemy
from config import settings

async def test():
    # Replace the host with the raw IPv6 address
    url = settings.database_url.replace("db.zaluzufofkddxnxiqvix.supabase.co", "[2406:da1a:314:7101:fc81:4869:6314:73fc]")
    # Also strip +asyncpg for the actual asyncpg connect call if needed, or just use SQLAlchemy
    print(f"Connecting to: {url}")
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            await conn.execute(org_sqlalchemy.text("SELECT 1"))
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
