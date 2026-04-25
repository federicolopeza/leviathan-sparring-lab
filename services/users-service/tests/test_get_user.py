from __future__ import annotations

from app.deps.auth import AuthUser
from httpx import AsyncClient


async def test_get_user_self_succeeds(
    client: AsyncClient,
    test_user: AuthUser,
    auth_headers: dict[str, str],
) -> None:
    response = await client.get(f"/v1/users/{test_user.id}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == test_user.id
    assert body["name"] == "Ada Lovelace"
    assert "email" not in body or body["email"] is None
    assert "is_admin" not in body or body["is_admin"] is None


async def test_get_user_idor_v_t3_002(
    client: AsyncClient,
    other_user: AuthUser,
    auth_headers: dict[str, str],
) -> None:
    # V-T3-002: no ownership check — any authenticated user can fetch any user profile
    response = await client.get(f"/v1/users/{other_user.id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == other_user.id
