"""Unit tests for NER agent — mocks HF API."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_ner_returns_drugs_and_conditions():
    mock_response = [
        {"word": "semaglutide", "entity_group": "Chemical", "score": 0.98},
        {"word": "obesity", "entity_group": "Disease", "score": 0.95},
        {"word": "metformin", "entity_group": "Drug", "score": 0.92},
    ]
    with patch("agents.ner.hf_post", new=AsyncMock(return_value=mock_response)):
        from agents.ner import run_ner
        result = await run_ner("Phase 2 trial of semaglutide for obesity with metformin")

    assert "semaglutide" in result["drugs"] or "metformin" in result["drugs"]
    assert "obesity" in result["conditions"]


@pytest.mark.asyncio
async def test_ner_handles_empty_text():
    from agents.ner import run_ner
    result = await run_ner("")
    assert result == {"drugs": [], "conditions": []}


@pytest.mark.asyncio
async def test_ner_handles_api_error():
    with patch("agents.ner.hf_post", new=AsyncMock(side_effect=Exception("API timeout"))):
        from agents.ner import run_ner
        result = await run_ner("some clinical trial text here for testing purposes")
    assert result["drugs"] == []
    assert result["conditions"] == []
