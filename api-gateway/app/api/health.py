"""
Health check endpoint.

Verifies connectivity to PostgreSQL and Redis.
"""

from fastapi import APIRouter, Depends
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """System health probe — checks DB and Redis connectivity."""
    checks: dict[str, str] = {}

    # PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = "healthy"
    except Exception as exc:
        checks["postgres"] = f"unhealthy: {exc}"

    # Redis
    try:
        if redis is None:
            checks["redis"] = "not_configured"
        else:
            pong = await redis.ping()
            checks["redis"] = "healthy" if pong else "unhealthy"
    except Exception as exc:
        checks["redis"] = f"unhealthy: {exc}"

    overall = all(v == "healthy" for v in checks.values())
    return {
        "status": "healthy" if overall else "degraded",
        "services": checks,
    }
