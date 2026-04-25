from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient


async def test_plans_list(
    client: AsyncClient,
    auth_headers: Callable[[str, str | None, bool], dict[str, str]],
) -> None:
    response = await client.get("/v1/billing/plans", headers=auth_headers("user-a"))

    assert response.status_code == 200
    assert [plan["code"] for plan in response.json()] == ["free", "pro", "enterprise"]
