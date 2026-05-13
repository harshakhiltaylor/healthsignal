import asyncio
from db.session import init_db

async def test():
    try:
        print("Initializing DB...")
        await init_db()
        print("Success! Database connected.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
