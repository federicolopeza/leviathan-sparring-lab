from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BIND_HOST: str = "0.0.0.0"
    BIND_PORT: int = 8080
    STS_TOKEN_TTL_S: int = 3600
    INSTANCE_ID: str = "i-0melispy12345678"
    ACCOUNT_ID: str = "123456789012"
    REGION: str = "us-east-1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
