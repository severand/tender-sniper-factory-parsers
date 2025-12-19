"""Scheduler Service - Task scheduling and queue management"""

from .celery_app import celery_app, task

__all__ = ["celery_app", "task"]
