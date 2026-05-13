"""
HuggingFace Serverless Inference API client.
Handles cold starts (503), rate limits, and retries automatically.
Free tier: ~30k chars/hr per model.
"""
import asyncio
import logging
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from config import settings

logger = logging.getLogger(__name__)

HF_BASE = "https://api-inference.huggingface.co/models"


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 503, 502, 500)
    return isinstance(exc, (httpx.TimeoutException, httpx.ConnectError))


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=3, max=30),
    retry=retry_if_exception(_is_retryable),
)
async def hf_post(model_id: str, payload: dict) -> dict | list:
    """
    POST to HF Inference API.
    Automatically retries on 503 (model loading / cold start).
    """
    url = f"{HF_BASE}/{model_id}"
    headers = {"Authorization": f"Bearer {settings.hf_token}"}

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=payload)

        if resp.status_code == 503:
            body = resp.json()
            wait = body.get("estimated_time", 10)
            logger.info(f"HF model {model_id} loading, waiting {wait:.1f}s...")
            await asyncio.sleep(min(wait, 20))
            raise httpx.HTTPStatusError("Model loading", request=resp.request, response=resp)

        resp.raise_for_status()
        return resp.json()
