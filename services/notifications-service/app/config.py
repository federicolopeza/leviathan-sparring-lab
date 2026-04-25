from __future__ import annotations

from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service settings.

    VULN V-T7-005: admin-tier MinIO root creds in service env — not scoped service account.
    """

    DATABASE_URL: str = "postgresql+asyncpg://melispy_app:changeme@postgres:5432/melispy_notifications"
    DATABASE_URL_AUTH: str = "postgresql+asyncpg://melispy_app:changeme@postgres:5432/melispy_auth"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_PUBLIC_KEY_PEM: str = ""
    BUILD_HASH: str = "dev"
    GIT_SHA: str = "dev"
    SERVICE_VERSION: str = "0.1.0"
    AUDIT_LOG_HMAC_KEY: str | None = None
    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_BUCKET: str = "uploads"
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_LOCAL_CACHE_DIR: str = "/tmp/melispy-notifications-minio"  # noqa: S108
    WKHTMLTOPDF_BIN: str = "wkhtmltopdf"
    MAGICK_BIN: str = "magick"
    SMTP_FROM: str = "no-reply@melispy.com"
    SMTP_LOG_ONLY: bool = True

    model_config = ConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
