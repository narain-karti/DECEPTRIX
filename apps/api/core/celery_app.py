import os
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
ALWAYS_EAGER = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "true").lower() == "true"

celery_app = Celery(
    "deceptrix_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["services.media_worker", "services.text_worker"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_always_eager=ALWAYS_EAGER,
    task_eager_propagates=True,
)
