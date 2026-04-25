from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient


async def test_add_member_admin_succeeds(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    create_org: Callable[[str | None], object],
    user_ids: dict[str, str],
) -> None:
    org = await create_org()
    admin_response = await client.post(
        f"/v1/orgs/{org['id']}/members",
        json={"user_id": user_ids["admin"], "role": "admin"},
        headers=auth_headers(user_ids["owner"]),
    )
    assert admin_response.status_code == 201

    response = await client.post(
        f"/v1/orgs/{org['id']}/members",
        json={"user_id": user_ids["member"], "role": "member"},
        headers=auth_headers(user_ids["admin"]),
    )

    assert response.status_code == 201
    assert response.json()["user_id"] == user_ids["member"]


async def test_remove_only_owner_forbidden(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    create_org: Callable[[str | None], object],
    user_ids: dict[str, str],
) -> None:
    org = await create_org()

    response = await client.delete(
        f"/v1/orgs/{org['id']}/members/{user_ids['owner']}",
        headers=auth_headers(user_ids["owner"]),
    )

    assert response.status_code == 409
