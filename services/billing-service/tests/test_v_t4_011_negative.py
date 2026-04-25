from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient


async def test_v_t4_011_negative_quantity_accepted(
    client: AsyncClient,
    auth_headers: Callable[[str, str | None, bool], dict[str, str]],
    pro_plan_id: str,
) -> None:
    headers = auth_headers("negative-user")
    cart = await client.post(
        "/v1/billing/cart",
        json={"plan_id": pro_plan_id, "quantity": -2},
        headers=headers,
    )
    checkout = await client.post("/v1/billing/checkout", json={}, headers=headers)

    assert cart.status_code == 200
    assert cart.json()["quantity"] == -2
    assert checkout.status_code == 200
    assert checkout.json()["total_cents"] == -1800
