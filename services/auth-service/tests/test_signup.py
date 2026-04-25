from __future__ import annotations

from app.deps.db import SessionLocal
from app.models import EmailVerifyToken, User
from httpx import AsyncClient
from sqlalchemy import select


async def test_signup_creates_user_and_verify_token(
    client: AsyncClient,
    signup_payload: dict[str, str],
) -> None:
    response = await client.post("/v1/auth/signup", json=signup_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["email_verify_required"] is True
    assert body["user_id"]

    async with SessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == "ada@example.com"))).scalar_one()
        token = (
            await db.execute(select(EmailVerifyToken).where(EmailVerifyToken.user_id == user.id))
        ).scalar_one()
        assert token.used_at is None


async def test_signup_duplicate_email_returns_409(
    client: AsyncClient,
    signup_payload: dict[str, str],
) -> None:
    first = await client.post("/v1/auth/signup", json=signup_payload)
    second = await client.post("/v1/auth/signup", json=signup_payload)

    assert first.status_code == 201
    assert second.status_code == 409
