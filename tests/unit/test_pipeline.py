"""Unit tests for ingestion normaliser."""
import pytest
from pipeline.ingest import _normalise, _extract_phase


def _make_raw(nct_id="NCT001", title="Test Trial", status="RECRUITING", phases=None):
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct_id, "briefTitle": title},
            "statusModule": {"overallStatus": status},
            "designModule": {"studyType": "INTERVENTIONAL", "phases": phases or ["PHASE2"]},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Acme Pharma"}},
            "conditionsModule": {"conditions": ["Obesity", "Diabetes"]},
            "armsInterventionsModule": {"interventions": [{"name": "Drug A"}]},
            "descriptionModule": {"briefSummary": "A Phase 2 trial."},
        }
    }


def test_normalise_extracts_nct_id():
    raw = _make_raw(nct_id="NCT12345678")
    result = _normalise(raw)
    assert result["id"] == "NCT12345678"


def test_normalise_extracts_conditions():
    raw = _make_raw()
    result = _normalise(raw)
    assert "Obesity" in result["condition"]
    assert "Diabetes" in result["condition"]


def test_normalise_extracts_phase():
    raw = _make_raw(phases=["PHASE2", "PHASE3"])
    result = _normalise(raw)
    assert "PHASE2" in result["phase"]


def test_normalise_handles_missing_fields():
    raw = {"protocolSection": {"identificationModule": {"nctId": "NCT000"}}}
    result = _normalise(raw)
    assert result["id"] == "NCT000"
    assert result["condition"] == ""


def test_extract_phase_empty():
    assert _extract_phase({}) is None


def test_extract_phase_single():
    result = _extract_phase({"phases": ["PHASE1"]})
    assert result == "PHASE1"
