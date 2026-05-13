"""Unit tests for deduplication logic."""
import pytest
from pipeline.dedup import fingerprint, title_hash, is_duplicate, needs_update


def test_fingerprint_is_deterministic():
    trial = {"id": "NCT12345678"}
    assert fingerprint(trial) == fingerprint(trial)


def test_fingerprint_differs_for_different_ids():
    assert fingerprint({"id": "NCT001"}) != fingerprint({"id": "NCT002"})


def test_title_hash_case_insensitive():
    a = title_hash({"title": "A Phase 2 Trial Of Drug X"})
    b = title_hash({"title": "a phase 2 trial of drug x"})
    assert a == b


@pytest.mark.asyncio
async def test_is_duplicate_exact_match():
    trial = {"id": "NCT001"}
    existing = {"NCT001", "NCT002"}
    assert await is_duplicate(trial, existing) is True


@pytest.mark.asyncio
async def test_is_not_duplicate_new_id():
    trial = {"id": "NCT999"}
    existing = {"NCT001", "NCT002"}
    assert await is_duplicate(trial, existing) is False


def test_needs_update_when_status_changed():
    class FakeTrial:
        status = "RECRUITING"
        phase = "PHASE2"

    trial_data = {"status": "COMPLETED", "phase": "PHASE2"}
    assert needs_update(trial_data, FakeTrial()) is True


def test_no_update_needed_when_unchanged():
    class FakeTrial:
        status = "RECRUITING"
        phase = "PHASE2"

    trial_data = {"status": "RECRUITING", "phase": "PHASE2"}
    assert needs_update(trial_data, FakeTrial()) is False
