# HealthSignal — Clinical Trial Intelligence Platform

A production-grade multi-agent AI system that monitors global clinical trial registries, extracts structured insights using HuggingFace models, evaluates output quality with a RAGAS/LLM-as-judge harness, and surfaces alerts to researchers via a semantic search dashboard.

**100% free-tier stack** — no credit card required.

## Architecture

```
ClinicalTrials.gov API  →  Celery Beat (nightly)
                         →  Dedup Worker (sentence similarity)
                         →  LangGraph Agent DAG:
                              ├─ NER Agent        (BioBERT, HF free)
                              ├─ ZSC Agent        (DeBERTa, HF free)
                              ├─ Summary Agent    (BART, HF free)
                              └─ Embed Agent      (PubMedBERT, HF free)
                         →  PGVector (Supabase free)
                         →  Judge Agent (Groq Llama3, free)
                         →  FastAPI + Next.js dashboard
```

## Free Tier Services Used

| Service | Provider | Free Limit |
|---|---|---|
| LLM inference | Groq (Llama 3.1 70B) | 6k req/day |
| HF model inference | HuggingFace Serverless | ~30k chars/hr |
| Vector DB | Supabase (pgvector) | 500MB |
| Task queue | Upstash Redis | 10k cmd/day |
| Hosting | Railway | $5 credit/mo |
| Eval framework | RAGAS (open source) | Unlimited |
| Observability | Prometheus + Grafana | Self-hosted |

## Quick Start

### 1. Clone and set up environment

```bash
git clone <your-repo>
cd healthsignal
cp .env.example .env
# Fill in your free-tier API keys (see .env.example)
```

### 2. Start backend services

```bash
cd backend
pip install -r requirements.txt
docker-compose up -d   # starts postgres+pgvector, redis, grafana
python -m alembic upgrade head
```

### 3. Run first ingestion

```bash
python -m pipeline.ingest --limit 100  # start small
```

### 4. Start API server

```bash
uvicorn api.main:app --reload --port 8000
```

### 5. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Project Structure

```
healthsignal/
├── backend/
│   ├── agents/          # LangGraph agent DAG
│   │   ├── router.py    # Coordinator / StateGraph entry
│   │   ├── ner.py       # BioBERT NER agent
│   │   ├── zsc.py       # Zero-shot classification agent
│   │   ├── summary.py   # BART summarisation agent
│   │   ├── embed.py     # PubMedBERT embedding agent
│   │   └── judge.py     # LLM-as-judge eval agent (Groq)
│   ├── api/
│   │   ├── main.py      # FastAPI app
│   │   ├── routes/      # search, alerts, eval endpoints
│   │   └── deps.py      # DB session, auth deps
│   ├── pipeline/
│   │   ├── ingest.py    # ClinicalTrials.gov fetcher
│   │   ├── dedup.py     # Sentence similarity dedup
│   │   ├── normalise.py # Field cleaning + schema mapping
│   │   └── tasks.py     # Celery tasks
│   ├── eval/
│   │   ├── ragas_eval.py   # RAGAS scoring pipeline
│   │   ├── judge_eval.py   # LLM-as-judge rubric
│   │   └── alerts.py       # Score regression alerting
│   ├── db/
│   │   ├── session.py   # SQLAlchemy async session
│   │   ├── models.py    # ORM models
│   │   └── migrations/  # Alembic migrations
│   ├── models/
│   │   └── schemas.py   # Pydantic request/response models
│   ├── celery_app.py
│   ├── config.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Dashboard home
│   │   ├── search/page.tsx  # Semantic search
│   │   └── evals/page.tsx   # Eval scores viewer
│   ├── components/
│   │   ├── TrialCard.tsx
│   │   ├── SearchBar.tsx
│   │   └── EvalChart.tsx
│   └── lib/
│       └── api.ts           # API client
├── infra/
│   ├── docker-compose.yml
│   ├── prometheus.yml
│   └── grafana/
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
│   ├── seed_trials.py       # Bootstrap with 1000 trials
│   └── run_eval.py          # Manual eval run
└── .env.example
```

## Getting API Keys (all free)

1. **Groq** — https://console.groq.com → free account → API key
2. **HuggingFace** — https://huggingface.co/settings/tokens → read token
3. **Supabase** — https://supabase.com → new project → connection string
4. **Upstash Redis** — https://upstash.com → free database → REST URL + token

## Eval Harness

Every RAG response is scored on:
- **Faithfulness** — does the answer stay grounded in retrieved context?
- **Answer relevance** — does it actually answer the question asked?
- **Context recall** — did retrieval surface the right trials?

Scores are written to the `eval_results` table. A GitHub Actions job runs the eval suite nightly and fails CI if faithfulness drops below 0.80.

## Resume Metrics You Can Claim

After running this for 2+ weeks you will have:
- 400k+ trial records indexed
- P95 semantic search latency benchmarks
- RAGAS faithfulness score on held-out test set
- LangSmith trace export showing agent latency breakdown
