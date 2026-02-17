"""
FinShield Risk Service — application entry point.

Lightweight FastAPI app that serves:
    - Health check endpoint
    - Loads the ML model at startup

The main work is done by the Celery worker (see app/tasks/).
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI

from app.ml.predictor import load_model

logger = structlog.get_logger("risk_service")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle."""
    logger.info("risk_service_starting")
    load_model()
    logger.info("risk_service_ready")
    yield
    logger.info("risk_service_stopped")


app = FastAPI(
    title="FinShield Risk Service",
    description="ML-powered fraud risk evaluation microservice",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    """Risk service health probe."""
    return {"status": "healthy", "service": "risk-service"}
