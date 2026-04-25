from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient


async def test_cart_create_and_replace(
    client: AsyncClient,
    auth_headers: Callable[[str, str | None, bool], dict[str, str]],
    pro_plan_id: str,
) -> None:
    headers = auth_headers("user-a")
    first = await client.post(
        "/v1/billing/cart",
        json={"plan_id": pro_plan_id, "quantity": 1},
        headers=headers,
    )
    second = await client.post(
        "/v1/billing/cart",
        json={"plan_id": pro_plan_id, "quantity": 3},
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] != second.json()["id"]
    assert second.json()["quantity"] == 3
    response = await client.get("/v1/billing/cart", headers=headers)
    assert response.json()["id"] == second.json()["id"]
