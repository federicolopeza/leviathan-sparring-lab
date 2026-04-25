from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    auth_service_url: str = Field(default="http://auth-service:8000", alias="AUTH_SERVICE_URL")
    users_service_url: str = Field(default="http://users-service:8000", alias="USERS_SERVICE_URL")
    orgs_service_url: str = Field(default="http://orgs-service:8000", alias="ORGS_SERVICE_URL")
    billing_service_url: str = Field(default="http://billing-service:8000", alias="BILLING_SERVICE_URL")
    uploads_service_url: str = Field(default="http://uploads-service:8000", alias="UPLOADS_SERVICE_URL")
    search_service_url: str = Field(default="http://search-service:8000", alias="SEARCH_SERVICE_URL")
    webhooks_service_url: str = Field(default="http://webhooks-service:8000", alias="WEBHOOKS_SERVICE_URL")

    jwt_public_key_pem: str = Field(default="", alias="JWT_PUBLIC_KEY_PEM")
    database_url_audit: str = Field(
        default="postgresql+asyncpg://melispy_app:changeme@postgres:5432/melispy_admin",
        alias="DATABASE_URL_AUDIT",
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    build_hash: str = Field(default="dev", alias="BUILD_HASH")
    git_sha: str = Field(default="unknown", alias="GIT_SHA")
    service_version: str = Field(default="0.1.0", alias="SERVICE_VERSION")
    audit_log_hmac_key: str = Field(default="dev-audit-key", alias="AUDIT_LOG_HMAC_KEY")

    tier_rate_limit_free: int = Field(default=60, alias="TIER_RATE_LIMIT_FREE")
    tier_rate_limit_pro: int = Field(default=600, alias="TIER_RATE_LIMIT_PRO")
    tier_rate_limit_enterprise: int = Field(default=6000, alias="TIER_RATE_LIMIT_ENTERPRISE")

    def tier_limits(self) -> dict[str, int]:
        return {
            "free": self.tier_rate_limit_free,
            "pro": self.tier_rate_limit_pro,
            "enterprise": self.tier_rate_limit_enterprise,
        }
