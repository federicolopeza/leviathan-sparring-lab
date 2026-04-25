from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from melispy_shared import issue_jwt

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL_AUTH"] = "sqlite+aiosqlite:///:memory:"
os.environ["BUILD_HASH"] = "test-build"
os.environ["GIT_SHA"] = "test-sha"
os.environ["SERVICE_VERSION"] = "test-version"
os.environ["MAX_RETRY_ATTEMPTS"] = "5"
os.environ["INITIAL_BACKOFF_MS"] = "1"


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

from app.deps.auth import AuthBase, AuthUser  # noqa: E402
from app.deps.db import AuthSessionLocal, auth_engine, engine  # noqa: E402
from app.main import app, rate_limit_store  # noqa: E402
from app.models import Base  # noqa: E402
from app.services.queue import webhook_queue  # noqa: E402


async def _insert_user(user_id: str, *, is_admin: bool = False) -> AuthUser:
    now = datetime.now(UTC)
    user = AuthUser(
        id=user_id,
        email=f"{user_id}@example.test",
        password_hash="unused",
        name=user_id,
        email_verified=True,
        is_admin=is_admin,
        created_at=now,
        updated_at=now,
    )
    async with AuthSessionLocal() as db:
        db.add(user)
        await db.commit()
    return user


@pytest.fixture(autouse=True)
async def reset_db() -> AsyncIterator[None]:
    rate_limit_store._buckets.clear()
    webhook_queue.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with auth_engine.begin() as conn:
        await conn.run_sync(AuthBase.metadata.drop_all)
        await conn.run_sync(AuthBase.metadata.create_all)
    yield


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def user_ids() -> dict[str, str]:
    return {
        "owner": "11111111-1111-1111-1111-111111111111",
        "other": "22222222-2222-2222-2222-222222222222",
        "admin": "33333333-3333-3333-3333-333333333333",
    }


@pytest.fixture
async def users(user_ids: dict[str, str]) -> dict[str, AuthUser]:
    return {
        "owner": await _insert_user(user_ids["owner"]),
        "other": await _insert_user(user_ids["other"]),
        "admin": await _insert_user(user_ids["admin"], is_admin=True),
    }


@pytest.fixture
def auth_headers(users: dict[str, AuthUser]) -> Callable[[str], dict[str, str]]:
    def _auth_headers(user_key: str) -> dict[str, str]:
        user = users[user_key]
        token = issue_jwt(
            {"sub": user.id, "sid": f"session-{user.id}"},
            JWT_PRIVATE_KEY_PEM,
            alg="RS256",
            expires_in=900,
        )
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers
