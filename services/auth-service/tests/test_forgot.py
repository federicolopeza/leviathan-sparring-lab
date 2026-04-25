from __future__ import annotations

from datetime import timedelta

from app.crud.tokens import hash_token
from app.crud.users import create_user, verify_password
from app.deps.db import SessionLocal
from app.models import PasswordResetToken, User
from app.models.base import now_utc
from httpx import AsyncClient
from sqlalchemy import select


async def test_forgot_always_returns_ok(client: AsyncClient) -> None:
    missing = await client.post("/v1/auth/forgot", json={"email": "missing@example.com"})

    async with SessionLocal() as db:
        await create_user(db, email="reset@example.com", password="oldpassword", name="Reset User")
        await db.commit()

    existing = await client.post("/v1/auth/forgot", json={"email": "reset@example.com"})

    assert missing.status_code == 200
    assert existing.status_code == 200
    assert missing.json() == {"ok": True}
    assert existing.json() == {"ok": True}
    async with SessionLocal() as db:
        token_count = len((await db.execute(select(PasswordResetToken))).scalars().all())
        assert token_count == 1


async def test_reset_with_valid_token_changes_password(client: AsyncClient) -> None:
    raw_token = "reset-token"
    async with SessionLocal() as db:
        user = await create_user(
            db,
            email="change@example.com",
            password="oldpassword",
            name="Reset User",
        )
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=now_utc() + timedelta(hours=1),
            )
        )
        await db.commit()

    response = await client.post(
        "/v1/auth/reset",
        json={"token": raw_token, "new_password": "newpassword123"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    async with SessionLocal() as db:
        refreshed = (
            await db.execute(select(User).where(User.email == "change@example.com"))
        ).scalar_one()
        assert verify_password("newpassword123", refreshed.password_hash)
