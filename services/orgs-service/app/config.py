from __future__ import annotations

from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://melispy_app:changeme@postgres:5432/melispy_orgs"
    DATABASE_URL_AUTH: str = "postgresql+asyncpg://melispy_app:changeme@postgres:5432/melispy_auth"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_PUBLIC_KEY_PEM: str = ""
    BUILD_HASH: str = "dev"
    GIT_SHA: str = "dev"
    SERVICE_VERSION: str = "0.1.0"
    AUDIT_LOG_HMAC_KEY: str | None = None
    INVITATION_TTL_DAYS: int = 7

    model_config = ConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
