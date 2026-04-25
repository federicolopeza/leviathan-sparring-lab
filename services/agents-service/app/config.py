from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://melispy_app:changeme@postgres:5432/melispy_agents"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_PUBLIC_KEY_PEM: str = ""
    BUILD_HASH: str = "dev"
    GIT_SHA: str = "dev"
    SERVICE_VERSION: str = "0.1.0"
    AUDIT_LOG_HMAC_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
