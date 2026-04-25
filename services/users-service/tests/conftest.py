from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from melispy_shared import issue_jwt

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:users_test?mode=memory&cache=shared&uri=true"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["DATABASE_URL_AUTH"] = TEST_DATABASE_URL
os.environ["BUILD_HASH"] = "test-build"
os.environ["GIT_SHA"] = "test-sha"
os.environ["SERVICE_VERSION"] = "test-version"


def _test_keypair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


PRIVATE_KEY_PEM, PUBLIC_KEY_PEM = _test_keypair()
os.environ["JWT_PUBLIC_KEY_PEM"] = PUBLIC_KEY_PEM

from app.deps.auth import AuthBase, AuthUser  # noqa: E402
from app.deps.db import AuthSessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture(autouse=True)
async def reset_db() -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(AuthBase.metadata.drop_all)
        await conn.run_sync(AuthBase.metadata.create_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def test_user_id() -> str:
    return str(uuid4())


@pytest.fixture
async def test_user(test_user_id: str) -> AuthUser:
    now = datetime.now(UTC)
    user = AuthUser(
        id=test_user_id,
        email="ada@example.com",
        password_hash="unused",
        name="Ada Lovelace",
        email_verified=True,
        is_admin=False,
        created_at=now,
        updated_at=now,
    )
    async with AuthSessionLocal() as db:
        db.add(user)
        await db.commit()
    return user


@pytest.fixture
async def other_user() -> AuthUser:
    now = datetime.now(UTC)
    user = AuthUser(
        id=str(uuid4()),
        email="other@example.com",
        password_hash="unused",
        name="Other User",
        email_verified=True,
        is_admin=False,
        created_at=now,
        updated_at=now,
    )
    async with AuthSessionLocal() as db:
        db.add(user)
        await db.commit()
    return user


@pytest.fixture
async def bearer_token(test_user: AuthUser) -> str:
    return issue_jwt({"sub": test_user.id, "email": test_user.email}, PRIVATE_KEY_PEM, alg="RS256")


@pytest.fixture
async def auth_headers(bearer_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {bearer_token}"}
