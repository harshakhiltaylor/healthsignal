"""
Judge Agent — LLM-as-judge using Groq Llama 3.1 70B (free tier).
Scores RAG responses on faithfulness, relevance, and groundedness.
Free: 6,000 requests/day on Groq.
"""
import json
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from config import settings

logger = logging.getLogger(__name__)

JUDGE_SYSTEM = """You are an expert evaluator for a biomedical RAG system.
Given a question, retrieved context from clinical trial records, and a generated answer,
score the answer on the following rubric. Respond ONLY with valid JSON.

Rubric:
- faithfulness (0.0-1.0): Is every claim in the answer supported by the context?
- relevance (0.0-1.0): Does the answer actually address the question?
- groundedness (0.0-1.0): Does the answer avoid hallucination and stay factual?

JSON format:
{
  "faithfulness": <float>,
  "relevance": <float>,
  "groundedness": <float>,
  "overall": <float>,
  "reasoning": "<one sentence explanation>"
}"""

JUDGE_TEMPLATE = """QUESTION: {question}

CONTEXT:
{context}

ANSWER:
{answer}

Score the answer using the rubric."""


def _get_groq_llm() -> ChatGroq:
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.0,
        max_tokens=2048,
    )


async def run_judge(question: str, context: str, answer: str) -> dict:
    """
    Score a RAG response using Groq Llama 3.1 70B.
    Returns dict with faithfulness, relevance, groundedness scores.
    """
    llm = _get_groq_llm()

    messages = [
        SystemMessage(content=JUDGE_SYSTEM),
        HumanMessage(content=JUDGE_TEMPLATE.format(
            question=question,
            context=context[:8000],  # use more context so all claims can be verified
            answer=answer,
        )),
    ]

    try:
        response = await llm.ainvoke(messages)
        raw = response.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        scores = json.loads(raw)
        logger.debug(f"Judge scores: {scores}")
        return scores

    except json.JSONDecodeError as e:
        logger.error(f"Judge response parse error: {e}")
        return {
            "faithfulness": 0.5,
            "relevance": 0.5,
            "groundedness": 0.5,
            "overall": 0.5,
            "reasoning": "Parse error — defaulting to 0.5",
        }
    except Exception as e:
        logger.error(f"Judge agent error: {e}")
        return {
            "faithfulness": 0.0,
            "relevance": 0.0,
            "groundedness": 0.0,
            "overall": 0.0,
            "reasoning": f"Error: {str(e)}",
        }


async def rag_query(question: str, context_chunks: list[str]) -> str:
    """
    Generate a RAG answer using Groq Llama 3.1 70B.
    Grounded answer based on retrieved trial chunks.
    """
    llm = _get_groq_llm()

    context = "\n\n---\n\n".join(context_chunks[:20])

    system = """You are HealthSignal AI — a friendly, expert clinical trial assistant.
Your task is to answer the user's question using ONLY the clinical trial records provided in the context below.

## How to write your answer:

### 1. Opening Summary (2-3 sentences)
Start with a warm, plain-English overview of what was found. Mention the number of trials and the general treatment landscape.

### 2. Trial Breakdown (bullet points per trial)
For each relevant trial write a bullet with:
- **Trial name** (and NCT ID in parentheses) — bold the title
- What the trial is studying (mechanism, drug, intervention)
- Phase and current status (Recruiting, Completed, etc.)
- Sponsor/institution
- Any notable detail from the summary (e.g. endpoints, patient population)

### 3. Key Insight (1-2 sentences)
Close with a brief takeaway about what the data collectively suggests about this treatment area.

## Strict rules:
- ONLY use information explicitly present in the provided context. Do NOT add background medical knowledge.
- If a detail (e.g. enrollment number, drug mechanism) is NOT in the context, do not include it.
- If no relevant trials are found in the context, say so honestly.
- Write in plain English — friendly but technically accurate."""

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=f"Clinical trial records (context):\n{context}\n\nUser question: {question}\n\nAnswer based strictly on the above context:"),
    ]

    try:
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        return f"Unable to generate answer: {str(e)}"
