"""
FastAPI application — main entry point.
Serves: search, RAG Q&A, eval, ingest status, health endpoints.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from config import settings
from db.session import init_db
from api.routes import search, rag, evals, ingest, health, trials

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting HealthSignal API...")
    try:
        await init_db()
        logger.info("Database ready")
    except Exception as e:
        logger.warning(f"Database not ready at startup (will retry on first request): {e}")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="HealthSignal API",
    description="Clinical Trial Intelligence Platform — free-tier AI stack",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler — ensures CORS headers are included even on 500 errors.
# Without this, unhandled exceptions return a plain 500 response that the browser
# blocks as a CORS error, causing "Failed to fetch" on the frontend.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {type(exc).__name__}"},
    )


# Mount Prometheus metrics at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(rag.router, prefix="/api", tags=["rag"])
app.include_router(evals.router, prefix="/api", tags=["evals"])
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(trials.router, prefix="/api", tags=["trials"])
