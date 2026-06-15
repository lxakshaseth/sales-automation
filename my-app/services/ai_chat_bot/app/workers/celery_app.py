import os

from celery import Celery

from app.core.config import REDIS_URL


def _redis_url(default_db: int) -> str:
    """
    Resolve Redis URLs for Celery services.

    Docker Compose injects CELERY_BROKER_URL and CELERY_RESULT_BACKEND. Local
    runs can still fall back to REDIS_URL, keeping configuration beginner-friendly.
    """
    base_url = REDIS_URL or "redis://redis:6379/0"
    if base_url.rsplit("/", 1)[-1].isdigit():
        return f"{base_url.rsplit('/', 1)[0]}/{default_db}"
    return base_url


celery_app = Celery(
    "ai_chat_bot",
    broker=os.getenv("CELERY_BROKER_URL") or _redis_url(1),
    backend=os.getenv("CELERY_RESULT_BACKEND") or _redis_url(2),
    include=[
        "app.queue.worker",
        "app.tasks.summary_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

# Celery's CLI auto-detects common attribute names when using
# `celery -A app.workers.celery_app ...`.
app = celery_app
celery = celery_app


@celery_app.task(name="healthcheck.ping")
def ping() -> str:
    """Small task used to verify Celery imports and Redis connectivity."""
    return "pong"
