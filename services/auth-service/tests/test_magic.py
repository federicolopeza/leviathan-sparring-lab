from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.crud.tokens import create_magic_link_token, hash_token
from app.crud.users import create_user
from app.deps.db import SessionLocal
from app.models import MagicLinkToken
from sqlalchemy import select


@pytest.mark.asyncio
async def test_magic_link_request_always_returns_ok(client: AsyncClient) -> None:
    resp_missing = await client.post("/v1/auth/magic/request", json={"email": "no-magic@example.com"})
    assert resp_missing.status_code == 200
    assert resp_missing.json() == {"ok": True}

    async with SessionLocal() as db:
        await create_user(db, email="magic-user@example.com", password="pass12345", name="Magic")
        await db.commit()

    resp_existing = await client.post("/v1/auth/magic/request", json={"email": "magic-user@example.com"})
    assert resp_existing.status_code == 200


@pytest.mark.asyncio
async def test_magic_link_login_issues_tokens(client: AsyncClient) -> None:
    async with SessionLocal() as db:
        user = await create_user(db, email="magic-login@example.com", password="pass12345", name="ML User")
        _row, raw = await create_magic_link_token(db, user.id)
        await db.commit()

    resp = await client.post("/v1/auth/magic/login", json={"token": raw})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body and body["access_token"]
    assert "refresh_token" in body


@pytest.mark.asyncio
async def test_magic_link_replay_within_24h_succeeds(client: AsyncClient) -> None:
    """V-T2-005 reproducer: same token works multiple times (used_at never set)."""
    async with SessionLocal() as db:
        user = await create_user(db, email="magic-replay@example.com", password="pass12345", name="Replay")
        _row, raw = await create_magic_link_token(db, user.id)
        await db.commit()

    first = await client.post("/v1/auth/magic/login", json={"token": raw})
    assert first.status_code == 200

    # V-T2-005: same token should succeed again (not consumed)
    second = await client.post("/v1/auth/magic/login", json={"token": raw})
    assert second.status_code == 200, (
        f"V-T2-005: replay should succeed but got {second.status_code}"
    )
    assert first.json()["access_token"] != second.json()["access_token"]  # new JWT each time


@pytest.mark.asyncio
async def test_magic_link_invalid_token_returns_401(client: AsyncClient) -> None:
    resp = await client.post("/v1/auth/magic/login", json={"token": "not-a-real-token"})
    assert resp.status_code == 401
