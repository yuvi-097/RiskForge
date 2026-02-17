"""
Redis-based sliding-window rate limiter middleware.

Tracks requests per authenticated user (or per IP for anonymous callers)
using a Redis key with TTL. Returns HTTP 429 when the limit is exceeded.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings
from app.core.logging import get_logger
from app.core.redis import redis_pool

logger = get_logger("rate_limiter")


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter backed by Redis."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting if Redis isn't available or for health checks
        if redis_pool is None or request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)

        # Identify the caller
        identifier = self._get_identifier(request)
        key = f"rate_limit:{identifier}"

        try:
            current = await redis_pool.incr(key)
            if current == 1:
                await redis_pool.expire(key, 60)  # 1-minute window

            if current > settings.rate_limit_per_minute:
                logger.warning("rate_limit_exceeded", identifier=identifier, count=current)
                return Response(
                    content='{"detail":"Rate limit exceeded. Try again later."}',
                    status_code=429,
                    media_type="application/json",
                )
        except Exception:
            # Fail-open: if Redis is down, allow the request
            logger.error("rate_limiter_redis_error", exc_info=True)

        response = await call_next(request)
        return response

    @staticmethod
    def _get_identifier(request: Request) -> str:
        """Extract a rate-limit key from the request.

        Uses the JWT subject (user id) if an Authorization header is present,
        otherwise falls back to the client IP.
        """
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from app.core.security import decode_access_token

                token = auth_header.split(" ", 1)[1]
                payload = decode_access_token(token)
                return payload.get("sub", request.client.host if request.client else "unknown")
            except Exception:
                pass
        return request.client.host if request.client else "unknown"
