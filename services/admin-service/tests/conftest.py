from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL_AUTH"] = "sqlite+aiosqlite:///:memory:"
os.environ["BUILD_HASH"] = "test-build"
os.environ["GIT_SHA"] = "test-sha"
os.environ["SERVICE_VERSION"] = "test-version"
os.environ["AUDIT_LOG_HMAC_KEY"] = "test-audit-key"


def _keypair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


JWT_PRIVATE_KEY_PEM, JWT_PUBLIC_KEY_PEM = _keypair()
os.environ["JWT_PUBLIC_KEY_PEM"] = JWT_PUBLIC_KEY_PEM

from app.deps.db import AuthSessionLocal, auth_engine, engine  # noqa: E402
from app.main import app, rate_limit_store  # noqa: E402
from app.models import AuthBase, AuthUser, Base  # noqa: E402
from melispy_shared import issue_jwt  # noqa: E402
from melispy_shared.models import Base as SharedBase  # noqa: E402


@pytest.fixture(autouse=True)
async def reset_db() -> AsyncIterator[None]:
    rate_limit_store._buckets.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(SharedBase.metadata.drop_all)
        await conn.run_sync(SharedBase.metadata.create_all)
        await conn.run_sync(Base.metadata.create_all)
    async with auth_engine.begin() as conn:
        await conn.run_sync(AuthBase.metadata.drop_all)
        await conn.run_sync(AuthBase.metadata.create_all)
    async with AuthSessionLocal() as auth_db:
        auth_db.add_all(
            [
                AuthUser(
                    id="11111111-1111-1111-1111-111111111111",
                    email="regular@example.com",
                    name="Regular User",
                    is_admin=False,
                    bio="plain bio",
                    created_at=datetime.now(UTC) - timedelta(days=2),
                    last_seen_at=datetime.now(UTC) - timedelta(hours=1),
                ),
                AuthUser(
                    id="22222222-2222-2222-2222-222222222222",
                    email="admin@example.com",
                    name="Admin User",
                    is_admin=True,
                    bio="<script>alert(1)</script>",
                    created_at=datetime.now(UTC) - timedelta(days=1),
                    last_seen_at=datetime.now(UTC),
                ),
            ]
        )
        await auth_db.commit()
    yield


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def auth_headers() -> Callable[[str, bool], dict[str, str]]:
    def _auth_headers(user_id: str, is_admin: bool = False) -> dict[str, str]:
        token = issue_jwt(
            {
                "sub": user_id,
                "sid": f"session-{user_id}",
                "user": {"is_admin": is_admin},
            },
            JWT_PRIVATE_KEY_PEM,
            alg="RS256",
            expires_in=900,
        )
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers


@pytest.fixture
def user_ids() -> dict[str, str]:
    return {
        "regular": "11111111-1111-1111-1111-111111111111",
        "admin": "22222222-2222-2222-2222-222222222222",
    }
