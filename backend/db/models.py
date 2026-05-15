from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from db.session import Base
from config import settings


class Trial(Base):
    __tablename__ = "trials"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # NCT number
    title: Mapped[str] = mapped_column(Text, nullable=False)
    official_title: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(64))
    phase: Mapped[str | None] = mapped_column(String(32))
    study_type: Mapped[str | None] = mapped_column(String(64))
    sponsor: Mapped[str | None] = mapped_column(String(256))
    condition: Mapped[str | None] = mapped_column(Text)
    intervention: Mapped[str | None] = mapped_column(Text)
    brief_summary: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[str | None] = mapped_column(String(32))
    completion_date: Mapped[str | None] = mapped_column(String(32))
    enrollment: Mapped[int | None] = mapped_column(Integer)
    raw_json: Mapped[dict | None] = mapped_column(JSON)

    # AI-extracted fields
    ai_summary: Mapped[str | None] = mapped_column(Text)
    extracted_drugs: Mapped[list | None] = mapped_column(JSON)
    extracted_conditions: Mapped[list | None] = mapped_column(JSON)
    therapeutic_area: Mapped[str | None] = mapped_column(String(128))
    zsc_confidence: Mapped[float | None] = mapped_column(Float)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    processed: Mapped[bool] = mapped_column(Boolean, default=False)

    chunks: Mapped[list["TrialChunk"]] = relationship(
        back_populates="trial", cascade="all, delete-orphan"
    )
    eval_results: Mapped[list["EvalResult"]] = relationship(back_populates="trial")


class TrialChunk(Base):
    __tablename__ = "trial_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trial_id: Mapped[str] = mapped_column(ForeignKey("trials.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.vector_dim))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    trial: Mapped["Trial"] = relationship(back_populates="chunks")


class EvalResult(Base):
    __tablename__ = "eval_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trial_id: Mapped[str | None] = mapped_column(ForeignKey("trials.id"), nullable=True)
    query: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    context: Mapped[str] = mapped_column(Text)
    faithfulness: Mapped[float | None] = mapped_column(Float)
    answer_relevance: Mapped[float | None] = mapped_column(Float)
    context_recall: Mapped[float | None] = mapped_column(Float)
    judge_score: Mapped[float | None] = mapped_column(Float)
    judge_reasoning: Mapped[str | None] = mapped_column(Text)
    eval_type: Mapped[str] = mapped_column(String(32), default="ragas")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    trial: Mapped["Trial | None"] = relationship(back_populates="eval_results")


class IngestLog(Base):
    __tablename__ = "ingest_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    trials_fetched: Mapped[int] = mapped_column(Integer, default=0)
    trials_new: Mapped[int] = mapped_column(Integer, default=0)
    trials_updated: Mapped[int] = mapped_column(Integer, default=0)
    trials_skipped: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="running")
    error_detail: Mapped[str | None] = mapped_column(Text)


class NewsletterCache(Base):
    __tablename__ = "newsletter_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    topics: Mapped[list] = mapped_column(JSON, nullable=False)
