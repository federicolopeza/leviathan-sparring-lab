from __future__ import annotations

from collections.abc import Callable

from app.deps.db import SessionLocal
from app.models import OrgMembership, OrgRole
from httpx import AsyncClient
from sqlalchemy import select


async def test_create_org_creates_owner_membership(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    response = await client.post(
        "/v1/orgs",
        json={"name": "Acme Security"},
        headers=auth_headers(user_ids["owner"]),
    )

    assert response.status_code == 201
    org = response.json()
    assert org["owner_user_id"] == user_ids["owner"]
    async with SessionLocal() as db:
        result = await db.execute(
            select(OrgMembership).where(
                OrgMembership.org_id == org["id"],
                OrgMembership.user_id == user_ids["owner"],
            )
        )
        membership = result.scalar_one()
    assert membership.role == OrgRole.OWNER


async def test_get_my_orgs_returns_member_orgs(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    create_org: Callable[[str | None], object],
    user_ids: dict[str, str],
) -> None:
    org = await create_org()
    add_response = await client.post(
        f"/v1/orgs/{org['id']}/members",
        json={"user_id": user_ids["member"], "role": "member"},
        headers=auth_headers(user_ids["owner"]),
    )
    assert add_response.status_code == 201

    response = await client.get("/v1/orgs/me", headers=auth_headers(user_ids["member"]))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [org["id"]]


async def test_get_org_member_can_view(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    create_org: Callable[[str | None], object],
    user_ids: dict[str, str],
) -> None:
    org = await create_org()
    await client.post(
        f"/v1/orgs/{org['id']}/members",
        json={"user_id": user_ids["member"], "role": "member"},
        headers=auth_headers(user_ids["owner"]),
    )

    response = await client.get(f"/v1/orgs/{org['id']}", headers=auth_headers(user_ids["member"]))

    assert response.status_code == 200
    assert response.json()["member_count"] == 2


async def test_get_org_non_member_returns_404(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    create_org: Callable[[str | None], object],
    user_ids: dict[str, str],
) -> None:
    org = await create_org()

    response = await client.get(f"/v1/orgs/{org['id']}", headers=auth_headers(user_ids["outsider"]))

    assert response.status_code == 404


async def test_patch_org_owner_can_update(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    create_org: Callable[[str | None], object],
    user_ids: dict[str, str],
) -> None:
    org = await create_org()

    response = await client.patch(
        f"/v1/orgs/{org['id']}",
        json={"name": "Acme Enterprise", "plan": "enterprise"},
        headers=auth_headers(user_ids["owner"]),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Acme Enterprise"
    assert response.json()["plan"] == "enterprise"


async def test_patch_org_member_forbidden(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    create_org: Callable[[str | None], object],
    user_ids: dict[str, str],
) -> None:
    org = await create_org()
    await client.post(
        f"/v1/orgs/{org['id']}/members",
        json={"user_id": user_ids["member"], "role": "member"},
        headers=auth_headers(user_ids["owner"]),
    )

    response = await client.patch(
        f"/v1/orgs/{org['id']}",
        json={"name": "Nope"},
        headers=auth_headers(user_ids["member"]),
    )

    assert response.status_code == 403
