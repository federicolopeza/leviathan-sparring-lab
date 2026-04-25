from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL_AUTH"] = "sqlite+aiosqlite:///:memory:"
os.environ["BUILD_HASH"] = "test-build"
os.environ["GIT_SHA"] = "test-sha"
os.environ["SERVICE_VERSION"] = "test-version"


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

from app.deps.db import SessionLocal, engine  # noqa: E402
from app.main import app, rate_limit_store  # noqa: E402
from app.models import Base  # noqa: E402
from melispy_shared import issue_jwt  # noqa: E402


@pytest.fixture(autouse=True)
async def reset_db() -> AsyncIterator[None]:
    rate_limit_store._buckets.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def auth_headers() -> Callable[[str], dict[str, str]]:
    def _auth_headers(user_id: str) -> dict[str, str]:
        token = issue_jwt(
            {"sub": user_id, "sid": f"session-{user_id}"},
            JWT_PRIVATE_KEY_PEM,
            alg="RS256",
            expires_in=900,
        )
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers


@pytest.fixture
def user_ids() -> dict[str, str]:
    return {
        "owner": "11111111-1111-1111-1111-111111111111",
        "admin": "22222222-2222-2222-2222-222222222222",
        "member": "33333333-3333-3333-3333-333333333333",
        "outsider": "44444444-4444-4444-4444-444444444444",
        "invitee": "55555555-5555-5555-5555-555555555555",
    }


@pytest.fixture
def db_session() -> Callable[[], AsyncIterator[object]]:
    return SessionLocal


@pytest.fixture
def create_org(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    user_ids: dict[str, str],
) -> Callable[[str | None], object]:
    async def _create_org(owner_user_id: str | None = None) -> dict[str, object]:
        owner_id = owner_user_id or user_ids["owner"]
        response = await client.post(
            "/v1/orgs",
            json={"name": "Acme Security", "plan": "pro", "region": "sa-east-1"},
            headers=auth_headers(owner_id),
        )
        assert response.status_code == 201
        return response.json()

    return _create_org
