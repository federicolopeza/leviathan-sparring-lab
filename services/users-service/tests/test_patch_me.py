from __future__ import annotations

from app.deps.db import SessionLocal
from app.models import UserProfile
from httpx import AsyncClient


async def test_patch_me_updates_bio(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.patch(
        "/v1/users/me",
        headers=auth_headers,
        json={"bio": "Analytical engine notes"},
    )

    assert response.status_code == 200
    assert response.json()["bio"] == "Analytical engine notes"


async def test_patch_me_mass_assignment_v_t3_003(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    # V-T3-003: is_admin accepted from user payload — privilege escalation
    response = await client.patch(
        "/v1/users/me",
        headers=auth_headers,
        json={"bio": "safe", "is_admin": True},
    )

    assert response.status_code == 200
    assert response.json()["is_admin"] is True
    async with SessionLocal() as db:
        profile = await db.get(UserProfile, response.json()["id"])
        assert profile is not None
        assert profile.bio == "safe"
