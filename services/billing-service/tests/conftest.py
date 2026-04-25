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
os.environ["DEFAULT_CURRENCY"] = "USD"


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

from app.crud.plans import seed_plans  # noqa: E402
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
    async with SessionLocal() as db:
        await seed_plans(db)
        await db.commit()
    yield


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client


@pytest.fixture
def auth_headers() -> Callable[[str, str | None, bool], dict[str, str]]:
    def _auth_headers(
        user_id: str,
        org_id: str | None = None,
        is_admin: bool = False,
    ) -> dict[str, str]:
        token = issue_jwt(
            {
                "sub": user_id,
                "sid": f"session-{user_id}",
                "org_id": org_id or f"org-{user_id}",
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
        "a": "11111111-1111-1111-1111-111111111111",
        "b": "22222222-2222-2222-2222-222222222222",
        "admin": "33333333-3333-3333-3333-333333333333",
    }


@pytest.fixture
async def pro_plan_id(
    client: AsyncClient,
    auth_headers: Callable[[str, str | None, bool], dict[str, str]],
) -> str:
    response = await client.get("/v1/billing/plans", headers=auth_headers("plan-user"))
    assert response.status_code == 200
    plans = response.json()
    return str(next(plan["id"] for plan in plans if plan["code"] == "pro"))


@pytest.fixture
def create_coupon(
    client: AsyncClient,
    auth_headers: Callable[[str, str | None, bool], dict[str, str]],
) -> Callable[[str, int | None, int | None], object]:
    async def _create_coupon(
        code: str = "SAVE10",
        discount_pct: int | None = 10,
        discount_cents: int | None = None,
    ) -> dict[str, object]:
        now = datetime.now(UTC)
        response = await client.post(
            "/v1/billing/coupons",
            json={
                "code": code,
                "discount_pct": discount_pct,
                "discount_cents": discount_cents,
                "valid_from": (now - timedelta(days=1)).isoformat(),
                "valid_until": (now + timedelta(days=1)).isoformat(),
                "max_uses": None,
            },
            headers=auth_headers("admin-user", is_admin=True),
        )
        assert response.status_code == 201
        return response.json()

    return _create_coupon


@pytest.fixture
def create_cart(
    client: AsyncClient,
    auth_headers: Callable[[str, str | None, bool], dict[str, str]],
    pro_plan_id: str,
) -> Callable[[str, int], object]:
    async def _create_cart(user_id: str = "cart-user", quantity: int = 1) -> dict[str, object]:
        response = await client.post(
            "/v1/billing/cart",
            json={"plan_id": pro_plan_id, "quantity": quantity},
            headers=auth_headers(user_id),
        )
        assert response.status_code == 200
        return response.json()

    return _create_cart
