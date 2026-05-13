import asyncio
from pipeline._ingest_runner import ingest_all

async def test():
    print("Running ingest_all directly...")
    await ingest_all()

if __name__ == "__main__":
    asyncio.run(test())
