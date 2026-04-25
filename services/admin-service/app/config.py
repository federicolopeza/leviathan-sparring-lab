from __future__ import annotations

from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://melispy_app:changeme@postgres:5432/melispy_admin"
    DATABASE_URL_AUTH: str = "postgresql+asyncpg://melispy_app:changeme@postgres:5432/melispy_auth"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_PUBLIC_KEY_PEM: str = ""
    BUILD_HASH: str = "dev"
    GIT_SHA: str = "dev"
    SERVICE_VERSION: str = "0.1.0"
    AUDIT_LOG_HMAC_KEY: str | None = None
    CLUSTER_INTERNAL_HEADER_TRUST: bool = True
    # V-T7-002 INTENTIONAL VULN: Vault root token stored in service env — readable post-RCE via /proc/1/environ
    VAULT_DEV_ROOT_TOKEN_ID: str = "dev-root-token"

    model_config = ConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
