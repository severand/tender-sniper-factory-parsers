"""Celery application configuration"""

from celery import Celery
from celery.schedules import crontab

from shared.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "tender_sniper",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    # Platform status check every minute
    "check-platforms-every-minute": {
        "task": "scheduler_service.tasks.check_platform_status",
        "schedule": crontab(minute="*"),
    },
}

# Define task decorator for easy registration
def task(*args, **kwargs):
    """Wrapper for Celery task decorator"""
    return celery_app.task(*args, **kwargs)