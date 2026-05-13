"""
Seed script — bootstrap the database with 1000 trials.
Run this first before testing the RAG endpoint.

Usage:
    cd backend
    python -m scripts.seed_trials --limit 1000

Takes ~20-40 minutes due to HF API rate limits.
Use --limit 100 for a quick test run.
"""
import asyncio
import argparse
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pipeline.ingest import fetch_trials
from pipeline._ingest_runner import ingest_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def seed(limit: int, query: str):
    logger.info(f"Seeding {limit} trials (query='{query or 'all'}')")
    max_pages = max(1, limit // 100)
    result = await ingest_all(query=query, max_pages=max_pages)
    logger.info(f"Seed complete: {result}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--query", type=str, default="")
    args = parser.parse_args()
    asyncio.run(seed(args.limit, args.query))
