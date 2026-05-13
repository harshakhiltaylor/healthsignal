from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "change_me"
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/healthsignal"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"

    # Groq (free LLM)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Clerk Auth
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    # HuggingFace (free serverless inference)
    hf_token: str = ""
    hf_ner_model: str = "d4data/biomedical-ner-all"
    hf_zsc_model: str = "cross-encoder/nli-deberta-v3-base"
    hf_summary_model: str = "facebook/bart-large-cnn"
    hf_embed_model: str = "NLP4Science/pubmedbert-large-uncased"

    # ClinicalTrials.gov API (no key needed)
    ct_api_base: str = "https://clinicaltrials.gov/api/v2"
    ct_batch_size: int = 100
    ct_max_pages: int = 50

    # Pipeline
    embed_chunk_size: int = 512
    embed_chunk_overlap: int = 50
    vector_dim: int = 768

    # Eval
    ragas_faithfulness_threshold: float = 0.80
    eval_sample_size: int = 50

    # LangSmith (optional tracing)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "healthsignal"

    # Observability ports
    prometheus_port: int = 9090
    grafana_port: int = 3001

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def celery_broker_url(self) -> str:
        return self.redis_url

    @property
    def celery_result_backend(self) -> str:
        return self.redis_url


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
