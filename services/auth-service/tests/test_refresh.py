from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_refresh_returns_new_tokens(client: AsyncClient) -> None:
    signup_payload = {
        "name": "Refresh User",
        "email": "refresh-user@example.com",
        "password": "correcthorse123",
        "org_name": "Refresh Org",
    }
    signup = await client.post("/v1/auth/signup", json=signup_payload)
    assert signup.status_code == 201, signup.text

    login = await client.post(
        "/v1/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    )
    assert login.status_code == 200, login.text
    refresh_token = login.json()["refresh_token"]

    response = await client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200, response.text
    body = response.json()
    assert "access_token" in body and body["access_token"]
    assert "refresh_token" in body and body["refresh_token"]
    assert body["refresh_token"] != refresh_token
    assert body["expires_in"] > 0


@pytest.mark.asyncio
async def test_refresh_rejects_old_rotated_token(client: AsyncClient) -> None:
    signup_payload = {
        "name": "Rotation User",
        "email": "rotation-user@example.com",
        "password": "correcthorse123",
        "org_name": "Rotation Org",
    }
    await client.post("/v1/auth/signup", json=signup_payload)
    login = await client.post(
        "/v1/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    )
    old_refresh = login.json()["refresh_token"]

    first = await client.post("/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert first.status_code == 200

    replay = await client.post("/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert replay.status_code == 401, replay.text
