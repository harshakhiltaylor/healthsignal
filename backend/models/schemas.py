from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TrialBase(BaseModel):
    id: str
    title: str
    status: Optional[str] = None
    phase: Optional[str] = None
    sponsor: Optional[str] = None
    condition: Optional[str] = None
    therapeutic_area: Optional[str] = None
    start_date: Optional[str] = None
    completion_date: Optional[str] = None
    enrollment: Optional[int] = None


class TrialDetail(TrialBase):
    official_title: Optional[str] = None
    intervention: Optional[str] = None
    brief_summary: Optional[str] = None
    ai_summary: Optional[str] = None
    extracted_drugs: Optional[list] = None
    extracted_conditions: Optional[list] = None
    zsc_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(default=10, ge=1, le=50)
    phase_filter: Optional[str] = None
    status_filter: Optional[str] = None
    therapeutic_area_filter: Optional[str] = None


class SearchResult(BaseModel):
    trial: TrialBase
    score: float
    chunk_text: str
    rank: int


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
    answer: Optional[str] = None


class RAGRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class RAGResponse(BaseModel):
    question: str
    answer: str
    sources: list[TrialBase]
    faithfulness_score: Optional[float] = None
    eval_id: Optional[int] = None


class EvalResultOut(BaseModel):
    id: int
    query: str
    faithfulness: Optional[float]
    answer_relevance: Optional[float]
    context_recall: Optional[float]
    judge_score: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


class EvalSummary(BaseModel):
    avg_faithfulness: float
    avg_answer_relevance: float
    avg_context_recall: float
    avg_judge_score: float
    total_evals: int
    below_threshold: int
    threshold: float


class IngestStatusOut(BaseModel):
    id: int
    run_at: datetime
    trials_fetched: int
    trials_new: int
    trials_updated: int
    trials_skipped: int
    errors: int
    duration_seconds: Optional[float]
    status: str

    model_config = {"from_attributes": True}
