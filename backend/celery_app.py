"""
Celery application — task queue for async pipeline jobs.
Uses Redis as broker (Upstash free tier or local Docker).
"""
from celery import Celery
from celery.schedules import crontab
from config import settings

celery_app = Celery(
    "healthsignal",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["pipeline.tasks"],
)

_ssl_config = {}
if settings.redis_url.startswith("rediss://"):
    import ssl as _ssl
    _ssl_config = {
        "broker_use_ssl": {"ssl_cert_reqs": _ssl.CERT_NONE},
        "redis_backend_use_ssl": {"ssl_cert_reqs": _ssl.CERT_NONE},
    }

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,  # 24h
    broker_connection_retry_on_startup=True,
    **_ssl_config,
)

# Nightly schedule — runs at 02:00 UTC every day
celery_app.conf.beat_schedule = {
    "nightly-ingest": {
        "task": "pipeline.tasks.run_nightly_ingest",
        "schedule": crontab(hour=2, minute=0),
    },
    "nightly-eval": {
        "task": "pipeline.tasks.run_nightly_eval",
        "schedule": crontab(hour=4, minute=0),
    },
}
