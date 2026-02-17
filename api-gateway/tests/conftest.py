"""
Pytest configuration and shared fixtures for the API Gateway test suite.

Uses an in-memory SQLite database (via aiosqlite) and mocked Redis
to avoid external dependencies during testing.
"""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.core.redis import get_redis
from app.models.base import Base

# Import all models so their tables are registered with Base.metadata
from app.models.user import User  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.alert import Alert  # noqa: F401


# ── Async event loop ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── In-memory async SQLite engine ─────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionFactory = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a fresh DB session for each test."""
    async with TestSessionFactory() as session:
        yield session


# ── Mock Redis ────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_redis():
    """Return a MagicMock that behaves like an async Redis client."""
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.setex = AsyncMock()
    r.incr = AsyncMock(return_value=1)
    r.expire = AsyncMock()
    r.ping = AsyncMock(return_value=True)
    return r


# ── HTTPX async test client ──────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(db_session: AsyncSession, mock_redis) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with overridden DB and Redis dependencies."""
    from app.main import app

    async def _override_db():
        yield db_session

    async def _override_redis():
        yield mock_redis

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_redis] = _override_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
