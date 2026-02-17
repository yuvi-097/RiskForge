"""
Celery client for the API Gateway.

This module ONLY creates a Celery app for *sending* tasks to the risk-service
broker. No workers run inside the api-gateway container.
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "riskforge",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="risk_queue",
    broker_connection_timeout=2,
    broker_connection_retry=False,
    broker_connection_retry_on_startup=False,
)
