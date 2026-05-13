"""
Summary Agent — BART-large-CNN for abstractive summarisation.
Compresses 2000-word protocol descriptions to 3-sentence plain-English summaries.
Uses HuggingFace free Serverless Inference API.
"""
import logging
from agents._hf_client import hf_post
from config import settings

logger = logging.getLogger(__name__)

MIN_LENGTH = 40
MAX_LENGTH = 130


async def run_summary(text: str) -> str:
    """
    Summarise trial description into 2-3 sentences.
    Falls back to truncated original text on error.
    """
    if not text or len(text.strip()) < 50:
        return text or ""

    # BART-large-CNN works best on 200–1024 tokens
    truncated = text[:3000]

    payload = {
        "inputs": truncated,
        "parameters": {
            "min_length": MIN_LENGTH,
            "max_length": MAX_LENGTH,
            "do_sample": False,
        },
    }

    try:
        result = await hf_post(settings.hf_summary_model, payload)
    except Exception as e:
        logger.error(f"Summary API error: {e}")
        return text[:300] + "..."

    if isinstance(result, list) and result:
        summary = result[0].get("summary_text", "")
        if summary:
            logger.debug(f"Summary: {len(summary)} chars")
            return summary

    return text[:300] + "..."
