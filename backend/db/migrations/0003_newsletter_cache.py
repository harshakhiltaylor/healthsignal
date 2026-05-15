"""
Migration 0003 — Create newsletter_cache table
Run via: python -m db.migrations.0003_newsletter_cache
Or apply manually in Supabase SQL editor.
"""
import asyncio
from sqlalchemy import text
from db.session import AsyncSessionLocal


SQL = """
CREATE TABLE IF NOT EXISTS newsletter_cache (
    id SERIAL PRIMARY KEY,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    topics JSONB NOT NULL
);
"""


async def up():
    async with AsyncSessionLocal() as db:
        await db.execute(text(SQL))
        await db.commit()
        print("✅ newsletter_cache table created.")


if __name__ == "__main__":
    asyncio.run(up())
