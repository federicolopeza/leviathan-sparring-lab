from __future__ import annotations

import hashlib
import time
from datetime import datetime, timedelta, timezone

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


async def test_forgot_timing_oracle_reveals_valid_email(client: AsyncClient) -> None:
    """V-T2-001 reproducer: valid email response takes ~600ms more than invalid."""
    async with SessionLocal() as db:
        await create_user(db, email="timing-victim@example.com", password="pass12345", name="Timing")
        await db.commit()

    t0 = time.monotonic()
    r_missing = await client.post("/v1/auth/forgot", json={"email": "no-such-user@example.com"})
    t1 = time.monotonic()
    r_existing = await client.post("/v1/auth/forgot", json={"email": "timing-victim@example.com"})
    t2 = time.monotonic()

    assert r_missing.status_code == 200
    assert r_existing.status_code == 200
    gap = (t2 - t1) - (t1 - t0)
    assert gap > 0.3, f"V-T2-001: expected >300ms timing gap, got {gap*1000:.0f}ms"


async def test_reset_token_predictable_given_email_and_timestamp(client: AsyncClient) -> None:
    """V-T2-002 reproducer: attacker recomputes sha1(email:iso_ts:BUILD_HASH)."""
    email = "predictable-reset@example.com"
    async with SessionLocal() as db:
        await create_user(db, email=email, password="pass12345", name="Predictable")
        await db.commit()

    before = datetime.now(tz=timezone.utc)
    await client.post("/v1/auth/forgot", json={"email": email})
    after = datetime.now(tz=timezone.utc)

    instance_salt = "test-build"  # BUILD_HASH set in conftest; in prod read from /v1/health/ready (V-T1-003)
    found: str | None = None
    ts = before
    while ts <= after + timedelta(seconds=2):
        candidate = hashlib.sha1(
            f"{email}:{ts.isoformat(timespec='seconds')}:{instance_salt}".encode()
        ).hexdigest()  # noqa: S324
        resp = await client.post(
            "/v1/auth/reset",
            json={"token": candidate, "new_password": "hackednewpass"},
        )
        if resp.status_code == 200:
            found = candidate
            break
        ts += timedelta(seconds=1)

    assert found is not None, "V-T2-002: predictable reset token not found within ±2s window"


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
