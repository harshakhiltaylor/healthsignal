"""
Deduplication using fast title hashing + HF sentence similarity.
Uses free HF Inference API for similarity scoring.
"""
import hashlib
import logging
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings

logger = logging.getLogger(__name__)

HF_SIMILARITY_URL = (
    f"https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
)


def fingerprint(trial: dict) -> str:
    """Deterministic hash of NCT ID — primary dedup key."""
    return hashlib.sha256(trial["id"].encode()).hexdigest()[:16]


def title_hash(trial: dict) -> str:
    """Normalised title hash for fuzzy dedup."""
    title = trial.get("title", "").lower().strip()
    return hashlib.md5(title.encode()).hexdigest()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
async def similarity_score(text_a: str, text_b: str) -> float:
    """
    Calls HF sentence similarity API (free).
    Returns cosine similarity 0.0–1.0.
    Falls back to 0.0 on error (conservative — won't drop records).
    """
    headers = {"Authorization": f"Bearer {settings.hf_token}"}
    payload = {"inputs": {"source_sentence": text_a, "sentences": [text_b]}}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                HF_SIMILARITY_URL, headers=headers, json=payload, timeout=20
            )
            if resp.status_code == 503:
                logger.warning("HF model loading (cold start), retrying...")
                raise Exception("Model loading")
            resp.raise_for_status()
            scores = resp.json()
            return float(scores[0]) if scores else 0.0
        except Exception as e:
            logger.error(f"Similarity API error: {e}")
            return 0.0


async def is_duplicate(trial: dict, existing_ids: set[str]) -> bool:
    """
    Fast path: check NCT ID (exact dedup).
    This is the primary dedup mechanism — NCT IDs are unique by definition.
    """
    return trial["id"] in existing_ids


def needs_update(trial: dict, existing_trial) -> bool:
    """
    Returns True if the trial status or phase changed
    since last ingestion — triggers a re-process.
    """
    if existing_trial is None:
        return True
    return (
        existing_trial.status != trial.get("status")
        or existing_trial.phase != trial.get("phase")
    )
