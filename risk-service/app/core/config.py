"""
Risk Service configuration — loaded from environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Risk service configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://riskforge:riskforge_secret_change_me@localhost:5432/riskforge"
    database_url_sync: str = "postgresql://riskforge:riskforge_secret_change_me@localhost:5432/riskforge"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # ML model path
    ml_model_path: str = "app/ml/model/fraud_model.joblib"

    # Server
    risk_service_host: str = "0.0.0.0"
    risk_service_port: int = 8001


settings = Settings()
