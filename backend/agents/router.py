"""
LangGraph Router Agent — StateGraph DAG coordinator.
Orchestrates: NER → ZSC → Summary (parallel) → Embed → Judge.
"""
from __future__ import annotations
import asyncio
import logging
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from agents.ner import run_ner
from agents.zsc import run_zsc
from agents.summary import run_summary
from agents.embed import run_embed

logger = logging.getLogger(__name__)


class TrialState(TypedDict):
    trial_id: str
    title: str
    condition: str
    intervention: str
    brief_summary: str
    phase: Optional[str]
    sponsor: Optional[str]
    start_date: Optional[str]
    completion_date: Optional[str]
    enrollment: Optional[int]

    # Agent outputs
    extracted_drugs: list
    extracted_conditions: list
    therapeutic_area: str
    zsc_confidence: float
    ai_summary: str
    embeddings_written: bool
    error: Optional[str]


async def _parallel_extract(state: TrialState) -> TrialState:
    """Run NER, ZSC, and Summary agents in parallel."""
    text = f"{state.get('title', '')} {state.get('condition', '')} {state.get('brief_summary', '')}"

    ner_task = asyncio.create_task(run_ner(text))
    zsc_task = asyncio.create_task(run_zsc(text))
    summary_task = asyncio.create_task(
        run_summary(state.get("brief_summary", "") or state.get("title", ""))
    )

    ner_result, zsc_result, summary_result = await asyncio.gather(
        ner_task, zsc_task, summary_task, return_exceptions=True
    )

    if isinstance(ner_result, Exception):
        logger.warning(f"NER failed for {state['trial_id']}: {ner_result}")
        ner_result = {"drugs": [], "conditions": []}

    if isinstance(zsc_result, Exception):
        logger.warning(f"ZSC failed: {zsc_result}")
        zsc_result = {"label": "Unknown", "confidence": 0.0}

    if isinstance(summary_result, Exception):
        logger.warning(f"Summary failed: {summary_result}")
        summary_result = state.get("brief_summary", "")[:300]

    return {
        **state,
        "extracted_drugs": ner_result.get("drugs", []),
        "extracted_conditions": ner_result.get("conditions", []),
        "therapeutic_area": zsc_result.get("label", "Unknown"),
        "zsc_confidence": zsc_result.get("confidence", 0.0),
        "ai_summary": summary_result,
    }


async def _embed_node(state: TrialState) -> TrialState:
    """Chunk text and write embeddings to PGVector."""
    # Build rich document — include all fields the model can later cite
    parts = []
    if state.get("title"):
        parts.append(f"Title: {state['title']}")
    if state.get("condition"):
        parts.append(f"Condition: {state['condition']}")
    if state.get("phase"):
        parts.append(f"Phase: {state['phase']}")
    if state.get("sponsor"):
        parts.append(f"Sponsor: {state['sponsor']}")
    if state.get("intervention"):
        parts.append(f"Interventions: {state['intervention']}")
    if state.get("start_date"):
        parts.append(f"Start Date: {state['start_date']}")
    if state.get("completion_date"):
        parts.append(f"Completion Date: {state['completion_date']}")
    if state.get("enrollment"):
        parts.append(f"Enrollment: {state['enrollment']} participants")
    if state.get("extracted_drugs"):
        parts.append(f"Drugs: {', '.join(state['extracted_drugs'])}")
    if state.get("extracted_conditions"):
        parts.append(f"Conditions (NER): {', '.join(state['extracted_conditions'])}")
    if state.get("ai_summary"):
        parts.append(f"Summary: {state['ai_summary']}")
    elif state.get("brief_summary"):
        parts.append(f"Summary: {state['brief_summary']}")

    text = "\n".join(parts)
    try:
        await run_embed(
            trial_id=state["trial_id"],
            text=text,
        )
        return {**state, "embeddings_written": True}
    except Exception as e:
        logger.error(f"Embed failed for {state['trial_id']}: {e}")
        return {**state, "embeddings_written": False, "error": str(e)}


async def _persist_node(state: TrialState) -> TrialState:
    """Write AI-extracted fields back to the Trial table."""
    from db.session import AsyncSessionLocal
    from db.models import Trial

    async with AsyncSessionLocal() as db:
        trial = await db.get(Trial, state["trial_id"])
        if trial:
            trial.extracted_drugs = state.get("extracted_drugs", [])
            trial.extracted_conditions = state.get("extracted_conditions", [])
            trial.therapeutic_area = state.get("therapeutic_area")
            trial.zsc_confidence = state.get("zsc_confidence")
            trial.ai_summary = state.get("ai_summary")
            trial.processed = True
            await db.commit()

    return state


def _build_graph() -> StateGraph:
    graph = StateGraph(TrialState)
    graph.add_node("extract", _parallel_extract)
    graph.add_node("embed", _embed_node)
    graph.add_node("persist", _persist_node)

    graph.set_entry_point("extract")
    graph.add_edge("extract", "embed")
    graph.add_edge("embed", "persist")
    graph.add_edge("persist", END)

    return graph.compile()


_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


async def run_agent_dag(trial_data: dict) -> TrialState:
    """
    Entry point — takes a raw trial dict and runs the full DAG.
    Returns the final state with all extracted fields.
    """
    initial_state: TrialState = {
        "trial_id": trial_data.get("id", ""),
        "title": trial_data.get("title", ""),
        "condition": trial_data.get("condition", ""),
        "intervention": trial_data.get("intervention", ""),
        "brief_summary": trial_data.get("brief_summary", ""),
        "phase": trial_data.get("phase"),
        "sponsor": trial_data.get("sponsor"),
        "start_date": trial_data.get("start_date"),
        "completion_date": trial_data.get("completion_date"),
        "enrollment": trial_data.get("enrollment"),
        "extracted_drugs": [],
        "extracted_conditions": [],
        "therapeutic_area": "",
        "zsc_confidence": 0.0,
        "ai_summary": "",
        "embeddings_written": False,
        "error": None,
    }

    graph = _get_graph()
    final_state = await graph.ainvoke(initial_state)
    return final_state
