"""
Celery application configuration for the Risk Service.

This module defines the Celery app that runs as a worker, consuming
tasks from the risk_queue.
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "riskforge_risk",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.risk_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="risk_queue",
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
