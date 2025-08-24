from __future__ import annotations

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application configuration loaded from environment."""

    app_host: str
    app_port: int
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    database_url: str
    redis_host: str
    redis_port: int
    redis_db: int
    minio_endpoint: str
    minio_root_user: str
    minio_root_password: str
    minio_bucket: str
    telegram_token: str
    telegram_webhook_url: str | None = None
    admin_token: str | None = None
    stars_api_key: str | None = None
    s3_endpoint: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket: str | None = None
    otlp_endpoint: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return application settings, logging presence of variables."""

    settings = Settings()  # type: ignore[call-arg]
    for name, value in settings.model_dump().items():
        logger.info(
            "Environment variable %s %s",
            name.upper(),
            "set" if value else "missing",
        )
    return settings
