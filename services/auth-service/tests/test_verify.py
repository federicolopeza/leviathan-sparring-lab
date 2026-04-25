from __future__ import annotations

from datetime import timedelta

from app.crud.tokens import hash_token
from app.crud.users import create_user
from app.deps.db import SessionLocal
from app.models import EmailVerifyToken, User
from app.models.base import now_utc
from httpx import AsyncClient


async def test_verify_marks_email_verified(client: AsyncClient) -> None:
    raw_token = "verify-token"
    async with SessionLocal() as db:
        user = await create_user(
            db,
            email="verify@example.com",
            password="password123",
            name="Verify User",
        )
        db.add(
            EmailVerifyToken(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=now_utc() + timedelta(hours=1),
            )
        )
        await db.commit()

    response = await client.post("/v1/auth/verify", json={"token": raw_token})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    async with SessionLocal() as db:
        refreshed = await db.get(User, user.id)
        assert refreshed is not None
        assert refreshed.email_verified is True
