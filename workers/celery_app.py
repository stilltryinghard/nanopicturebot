import sys

sys.path.insert(0, "/app")

from celery import Celery
from core.config import settings
from celery.schedules import crontab

celery_app = Celery(
    "ai_image_bot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    # Периодические задачи
    beat_schedule={
        "check-low-balance": {
            "task": "workers.tasks.check_low_balance",
            "schedule": crontab(hour="12", minute="0"),  # каждый день в 12:00
        },
    },
)
