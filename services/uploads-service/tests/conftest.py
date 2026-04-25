from __future__ import annotations

import os
import shutil
from collections.abc import AsyncIterator, Callable
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL_AUTH"] = "sqlite+aiosqlite:///:memory:"
os.environ["BUILD_HASH"] = "test-build"
os.environ["GIT_SHA"] = "test-sha"
os.environ["SERVICE_VERSION"] = "test-version"
os.environ["MINIO_ENDPOINT"] = "local"
os.environ["MAX_UPLOAD_BYTES"] = "64"


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

from app.config import get_settings  # noqa: E402
from app.database import SessionLocal, engine  # noqa: E402
from app.main import app, rate_limit_store  # noqa: E402
from app.models import Base  # noqa: E402
from melispy_shared import issue_jwt  # noqa: E402


@pytest.fixture(autouse=True)
async def reset_db() -> AsyncIterator[None]:
    cache_dir = Path(".test-cache")
    if cache_dir.exists():  # noqa: ASYNC240
        shutil.rmtree(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)  # noqa: ASYNC240
    os.environ["MINIO_LOCAL_CACHE_DIR"] = str(cache_dir)
    get_settings.cache_clear()
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
        "a": "11111111-1111-1111-1111-111111111111",
        "b": "22222222-2222-2222-2222-222222222222",
    }


@pytest.fixture
def db_session() -> Callable[[], AsyncIterator[object]]:
    return SessionLocal
