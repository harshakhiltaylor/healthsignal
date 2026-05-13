import asyncio
from agents.embed import _embed_text

async def main():
    res = await _embed_text("What Phase 3 trials are studying Alzheimer's disease?")
    print("Embedding result length:", len(res) if res else None)
    if res is None:
        print("Embedding failed.")

if __name__ == "__main__":
    asyncio.run(main())
