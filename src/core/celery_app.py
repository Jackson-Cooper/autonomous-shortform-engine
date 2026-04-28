from celery import Celery
from src.core.config import settings

celery_app = Celery(
    "content_engine",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "src.tasks.orchestrator.*": {"queue": "orchestrator_queue"},
    },
)

celery_app.autodiscover_tasks(["src.tasks.orchestrator"])
