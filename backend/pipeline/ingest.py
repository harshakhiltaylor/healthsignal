"""
Ingestion pipeline — ClinicalTrials.gov v2 API
Free, no API key required.
"""
import asyncio
import logging
from typing import AsyncGenerator
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings

logger = logging.getLogger(__name__)

CT_FIELDS = (
    "NCTId,BriefTitle,OfficialTitle,OverallStatus,Phase,StudyType,"
    "LeadSponsorName,Condition,InterventionName,BriefSummary,"
    "StartDate,CompletionDate,EnrollmentCount"
)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _fetch_page(client: httpx.AsyncClient, page_token: str | None, query: str = "") -> dict:
    params = {
        "format": "json",
        "pageSize": settings.ct_batch_size,
        "fields": CT_FIELDS,
    }
    if query:
        params["query.term"] = query
    if page_token:
        params["pageToken"] = page_token

    resp = await client.get(f"{settings.ct_api_base}/studies", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


async def fetch_trials(query: str = "", max_pages: int | None = None) -> AsyncGenerator[dict, None]:
    """
    Async generator — yields raw trial dicts one page at a time.
    Handles pagination automatically using nextPageToken.
    """
    max_pages = max_pages or settings.ct_max_pages
    page_token = None
    pages_fetched = 0

    async with httpx.AsyncClient() as client:
        while pages_fetched < max_pages:
            data = await _fetch_page(client, page_token, query)
            studies = data.get("studies", [])

            if not studies:
                break

            for study in studies:
                yield _normalise(study)

            page_token = data.get("nextPageToken")
            if not page_token:
                break

            pages_fetched += 1
            await asyncio.sleep(0.2)  # polite rate limiting


async def fetch_trial_results(nct_id: str, client: httpx.AsyncClient) -> str | None:
    """
    Fetch outcome/results summary for a completed trial from ClinicalTrials.gov v2 API.
    Returns a plain-text summary of primary outcomes if available.
    """
    try:
        resp = await client.get(
            f"{settings.ct_api_base}/studies/{nct_id}",
            params={"format": "json", "fields": "ResultsSection"},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        results = data.get("resultsSection", {})
        if not results:
            return None

        parts = []
        # Outcome measures
        outcomes = results.get("outcomeMeasuresModule", {}).get("outcomeMeasures", [])
        for om in outcomes[:3]:  # top 3 outcomes
            title = om.get("title", "")
            description = om.get("description", "")
            if title:
                parts.append(f"Outcome: {title}. {description}")

        # Adverse events summary
        ae = results.get("adverseEventsModule", {})
        serious_ae = ae.get("seriousEvents", [])
        if serious_ae:
            parts.append(f"Serious adverse events reported: {len(serious_ae)} types.")

        return " ".join(parts) if parts else None
    except Exception as e:
        logger.debug(f"Could not fetch results for {nct_id}: {e}")
        return None


def _normalise(raw: dict) -> dict:
    """Map ClinicalTrials.gov v2 JSON to our flat schema."""
    proto = raw.get("protocolSection", {})
    id_mod = proto.get("identificationModule", {})
    status_mod = proto.get("statusModule", {})
    design_mod = proto.get("designModule", {})
    sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
    conditions_mod = proto.get("conditionsModule", {})
    interventions_mod = proto.get("armsInterventionsModule", {})
    desc_mod = proto.get("descriptionModule", {})

    interventions = interventions_mod.get("interventions", [])
    intervention_names = [i.get("name", "") for i in interventions if i.get("name")]

    return {
        "id": id_mod.get("nctId", ""),
        "title": id_mod.get("briefTitle", ""),
        "official_title": id_mod.get("officialTitle"),
        "status": status_mod.get("overallStatus"),
        "phase": _extract_phase(design_mod),
        "study_type": design_mod.get("studyType"),
        "sponsor": sponsor_mod.get("leadSponsor", {}).get("name"),
        "condition": ", ".join(conditions_mod.get("conditions", [])),
        "intervention": ", ".join(intervention_names),
        "brief_summary": desc_mod.get("briefSummary"),
        "start_date": status_mod.get("startDateStruct", {}).get("date"),
        "completion_date": status_mod.get("completionDateStruct", {}).get("date"),
        "enrollment": design_mod.get("enrollmentInfo", {}).get("count"),
        "raw_json": raw,
    }


def _extract_phase(design_mod: dict) -> str | None:
    phases = design_mod.get("phases", [])
    if phases:
        return " / ".join(phases)
    return None
