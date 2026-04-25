from __future__ import annotations

from httpx import AsyncClient


async def test_me_returns_user_with_profile(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.get("/v1/users/me", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "ada@example.com"
    assert body["name"] == "Ada Lovelace"
    assert body["bio"] is None
    assert body["avatar_url"] is None
    assert body["is_admin"] is False
    assert body["created_at"]


async def test_me_requires_bearer(client: AsyncClient) -> None:
    response = await client.get("/v1/users/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not Found"}
