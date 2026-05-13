"""
Zero-Shot Classification Agent — DeBERTa NLI model.
Tags trials into therapeutic areas without fine-tuning.
Uses HuggingFace free Serverless Inference API.
"""
import logging
from agents._hf_client import hf_post
from config import settings

logger = logging.getLogger(__name__)

THERAPEUTIC_AREAS = [
    "Oncology",
    "Cardiology",
    "Neurology",
    "Infectious Disease",
    "Endocrinology and Metabolism",
    "Immunology and Rheumatology",
    "Respiratory Medicine",
    "Gastroenterology",
    "Dermatology",
    "Psychiatry and Mental Health",
    "Rare Disease",
    "Ophthalmology",
    "Nephrology",
    "Hematology",
    "Musculoskeletal",
    "Women's Health",
    "Pediatrics",
    "Geriatrics",
    "Pain Management",
    "Other",
]


async def run_zsc(text: str) -> dict:
    """
    Classify trial text into a therapeutic area.
    Returns {'label': str, 'confidence': float}.
    """
    if not text or len(text.strip()) < 10:
        return {"label": "Other", "confidence": 0.0}

    truncated = text[:1500]

    payload = {
        "inputs": truncated,
        "parameters": {
            "candidate_labels": THERAPEUTIC_AREAS,
            "multi_label": False,
        },
    }

    try:
        result = await hf_post(settings.hf_zsc_model, payload)
    except Exception as e:
        logger.error(f"ZSC API error: {e}")
        return {"label": "Other", "confidence": 0.0}

    if isinstance(result, dict) and "labels" in result and "scores" in result:
        top_label = result["labels"][0]
        top_score = result["scores"][0]
        logger.debug(f"ZSC: {top_label} ({top_score:.2f})")
        return {"label": top_label, "confidence": round(top_score, 4)}

    return {"label": "Other", "confidence": 0.0}
