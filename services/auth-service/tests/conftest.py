from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["BUILD_HASH"] = "test-build"
os.environ["GIT_SHA"] = "test-sha"
os.environ["SERVICE_VERSION"] = "test-version"

from app.deps.db import engine  # noqa: E402
from app.main import _rate_store, app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture(autouse=True)
async def reset_db() -> AsyncIterator[None]:
    _rate_store._buckets.clear()  # reset sliding window so rate limit never fires in tests
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
def signup_payload() -> dict[str, str]:
    return {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "password": "correct horse battery staple",
        "org_name": "Analytical Engines",
    }
