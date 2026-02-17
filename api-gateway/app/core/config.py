"""
RiskForge API Gateway — Application Settings.

All configuration is loaded from environment variables via Pydantic BaseSettings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ──────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://riskforge:riskforge_secret_change_me@localhost:5432/riskforge"
    database_url_sync: str = "postgresql://riskforge:riskforge_secret_change_me@localhost:5432/riskforge"

    # ── Redis ─────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── JWT ───────────────────────────────────────────────────────────
    jwt_secret_key: str = "CHANGE_ME_TO_A_RANDOM_64_CHAR_HEX_STRING"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # ── Celery ────────────────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # ── Rate Limiting ─────────────────────────────────────────────────
    rate_limit_per_minute: int = 60

    # ── Server ────────────────────────────────────────────────────────
    api_gateway_host: str = "0.0.0.0"
    api_gateway_port: int = 8000


settings = Settings()
