"""
Async Redis connection pool and FastAPI dependency.

Redis is optional for local development — if unavailable, the system
continues to work without caching or rate limiting.
"""

from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
import structlog

from app.core.config import settings

logger = structlog.get_logger("redis")

redis_pool: aioredis.Redis | None = None


async def init_redis() -> aioredis.Redis | None:
    """Initialise the module-level Redis connection pool.

    Returns None and logs a warning if Redis is unreachable (local dev).
    """
    global redis_pool  # noqa: PLW0603
    try:
        pool = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=50,
        )
        await pool.ping()  # verify connectivity
        redis_pool = pool
        logger.info("redis_connected", url=settings.redis_url)
        return redis_pool
    except Exception as exc:
        logger.warning("redis_unavailable", error=str(exc), msg="Running without Redis")
        redis_pool = None
        return None


async def close_redis() -> None:
    """Close the Redis connection pool gracefully."""
    global redis_pool  # noqa: PLW0603
    if redis_pool:
        await redis_pool.aclose()
        redis_pool = None


async def get_redis() -> AsyncGenerator[aioredis.Redis | None, None]:
    """FastAPI dependency – yields the shared Redis client (or None)."""
    yield redis_pool

