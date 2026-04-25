from __future__ import annotations

from functools import lru_cache

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import ConfigDict, model_validator
from pydantic_settings import BaseSettings

_EPHEMERAL_PRIVATE_KEY: str | None = None
_EPHEMERAL_PUBLIC_KEY: str | None = None


def _ephemeral_keypair() -> tuple[str, str]:
    global _EPHEMERAL_PRIVATE_KEY, _EPHEMERAL_PUBLIC_KEY
    if _EPHEMERAL_PRIVATE_KEY and _EPHEMERAL_PUBLIC_KEY:
        return _EPHEMERAL_PRIVATE_KEY, _EPHEMERAL_PUBLIC_KEY
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _EPHEMERAL_PRIVATE_KEY = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    _EPHEMERAL_PUBLIC_KEY = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return _EPHEMERAL_PRIVATE_KEY, _EPHEMERAL_PUBLIC_KEY


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://melispy_app:changeme@postgres:5432/melispy_auth"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_PRIVATE_KEY_PEM: str | None = None
    JWT_PUBLIC_KEY_PEM: str | None = None
    JWT_LEGACY_HS256_SECRET: str | None = None
    BCRYPT_ROUNDS: int = 12
    COOKIE_DOMAIN: str = ".melispy.com"  # V-T3-005 INTENTIONAL VULN: wide cookie domain
    BUILD_HASH: str = "dev"
    GIT_SHA: str = "dev"
    SERVICE_VERSION: str = "0.1.0"
    AUDIT_LOG_HMAC_KEY: str | None = None
    INSTANCE_SALT: str = ""  # V-T2-002 chain: defaults to BUILD_HASH; recoverable via V-T1-003 /ready leak

    model_config = ConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def ensure_jwt_keypair(self) -> Settings:
        if not (self.JWT_PRIVATE_KEY_PEM and self.JWT_PUBLIC_KEY_PEM):
            private_key, public_key = _ephemeral_keypair()
            self.JWT_PRIVATE_KEY_PEM = self.JWT_PRIVATE_KEY_PEM or private_key
            self.JWT_PUBLIC_KEY_PEM = self.JWT_PUBLIC_KEY_PEM or public_key
        # V-T2-002 chain: INSTANCE_SALT == BUILD_HASH when not explicitly overridden
        if not self.INSTANCE_SALT:
            self.INSTANCE_SALT = self.BUILD_HASH
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
