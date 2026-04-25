from __future__ import annotations

import os
from collections import defaultdict
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import httpx
import pytest
import pytest_asyncio
from app.config import Settings
from app.deps.db import create_audit_engine
from app.main import create_app
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from melispy_shared import Base, issue_jwt
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


class FakeRedis:
    def __init__(self) -> None:
        self.zsets: dict[str, dict[str, float]] = defaultdict(dict)

    async def zremrangebyscore(self, key: str, minimum: float, maximum: float) -> None:
        self.zsets[key] = {
            member: score
            for member, score in self.zsets[key].items()
            if not minimum <= score <= maximum
        }

    async def zcard(self, key: str) -> int:
        return len(self.zsets[key])

    async def zadd(self, key: str, values: dict[str, float]) -> None:
        self.zsets[key].update(values)

    async def expire(self, key: str, seconds: int) -> None:
        _ = key, seconds


@dataclass(frozen=True)
class GatewayHarness:
    app: Any
    audit_sessionmaker: async_sessionmaker[AsyncSession]


@pytest.fixture
def rsa_keys() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


@pytest.fixture
def token_factory(rsa_keys: tuple[str, str]) -> Callable[..., str]:
    private_pem, _ = rsa_keys

    def make_token(
        user_id: str = "user-1",
        session_id: str = "session-1",
        org_id: str = "org-1",
        tier: str = "free",
    ) -> str:
        return issue_jwt(
            {
                "sub": user_id,
                "user_id": user_id,
                "session_id": session_id,
                "org_id": org_id,
                "email": f"{user_id}@example.test",
                "tier": tier,
            },
            private_pem,
        )

    return make_token


@pytest.fixture
def settings(rsa_keys: tuple[str, str], monkeypatch: pytest.MonkeyPatch) -> Settings:
    _, public_pem = rsa_keys
    monkeypatch.setenv("AUDIT_LOG_HMAC_KEY", "test-audit-key")
    return Settings(
        AUTH_SERVICE_URL="http://auth-service:8000",
        USERS_SERVICE_URL="http://users-service:8000",
        ORGS_SERVICE_URL="http://orgs-service:8000",
        JWT_PUBLIC_KEY_PEM=public_pem,
        DATABASE_URL_AUDIT="sqlite+aiosqlite:///:memory:",
        REDIS_URL="redis://redis:6379/9",
        BUILD_HASH="build-test",
        GIT_SHA="git-test",
        SERVICE_VERSION="test-version",
        TIER_RATE_LIMIT_FREE=2,
        TIER_RATE_LIMIT_PRO=4,
        TIER_RATE_LIMIT_ENTERPRISE=10,
    )


@pytest_asyncio.fixture
async def gateway_harness(settings: Settings) -> AsyncIterator[GatewayHarness]:
    engine = create_audit_engine(settings.database_url_audit)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    app = create_app(settings=settings, redis_client=FakeRedis(), audit_sessionmaker=sessionmaker)
    try:
        yield GatewayHarness(app=app, audit_sessionmaker=sessionmaker)
    finally:
        await _dispose(engine)


@pytest_asyncio.fixture
async def client(gateway_harness: GatewayHarness) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=gateway_harness.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client


async def _dispose(engine: AsyncEngine) -> None:
    await engine.dispose()
