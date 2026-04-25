from __future__ import annotations

from app.crud.users import create_user
from app.deps.db import SessionLocal
from app.models import Session
from httpx import AsyncClient
from sqlalchemy import select


async def test_login_returns_jwt(client: AsyncClient) -> None:
    async with SessionLocal() as db:
        await create_user(db, email="login@example.com", password="password123", name="Login User")
        await db.commit()

    response = await client.post(
        "/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"].count(".") == 2
    assert body["refresh_token"]
    assert body["expires_in"] == 900
    assert body["user"]["email"] == "login@example.com"


async def test_login_invalid_creds_returns_401_generic(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/auth/login",
        json={"email": "missing@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not Found"}


async def test_logout_revokes_session(client: AsyncClient) -> None:
    async with SessionLocal() as db:
        await create_user(
            db,
            email="logout@example.com",
            password="password123",
            name="Logout User",
        )
        await db.commit()

    login = await client.post(
        "/v1/auth/login",
        json={"email": "logout@example.com", "password": "password123"},
    )
    token = login.json()["access_token"]
    response = await client.post("/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 204
    async with SessionLocal() as db:
        session = (await db.execute(select(Session))).scalar_one()
        assert session.revoked_at is not None
