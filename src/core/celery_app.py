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
        "src.tasks.discovery.*": {"queue": "discovery_queue"},
        "src.tasks.llm.*": {"queue": "llm_queue"},
        "src.tasks.tts.*": {"queue": "tts_queue"},
        "src.tasks.video.*": {"queue": "video_render_queue"},
        "src.tasks.publishing.*": {"queue": "publishing_queue"},
    },
)

# Optional: Autodiscover tasks
celery_app.autodiscover_tasks(["src.tasks.discovery", "src.tasks.llm", "src.tasks.tts", "src.tasks.video", "src.tasks.publishing"])
