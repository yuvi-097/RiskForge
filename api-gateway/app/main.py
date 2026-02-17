"""
RiskForge API Gateway — Application entry point.

Configures the FastAPI instance, registers routers and middleware,
and manages the application lifespan (DB & Redis initialisation).
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api import auth, alerts, health, transactions
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.redis import close_redis, init_redis
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware

logger = get_logger("main")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Manage startup / shutdown resources."""
    setup_logging()
    logger.info("api_gateway_starting")

    # Auto-create tables for SQLite (local dev) — production uses Alembic
    if settings.database_url.startswith("sqlite"):
        from app.core.database import engine
        from app.models.base import Base
        from app.models import user, transaction, alert  # noqa: F401 — register models

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("sqlite_tables_created")

    # Initialise Redis pool (gracefully handles connection failure)
    await init_redis()

    yield  # Application runs here

    # Shutdown
    await close_redis()
    logger.info("api_gateway_stopped")


app = FastAPI(
    title="RiskForge API Gateway",
    description="Financial Risk & Fraud Detection — API Gateway Service",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware (outermost first) ──────────────────────────────────────────────
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimiterMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
API_V1 = "/api/v1"
app.include_router(health.router)
app.include_router(auth.router, prefix=API_V1)
app.include_router(transactions.router, prefix=API_V1)
app.include_router(alerts.router, prefix=API_V1)
