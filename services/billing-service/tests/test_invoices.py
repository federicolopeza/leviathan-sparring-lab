from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient


async def test_invoices_list_only_own(
    client: AsyncClient,
    auth_headers: Callable[[str, str | None, bool], dict[str, str]],
    create_cart: Callable[[str, int], object],
    user_ids: dict[str, str],
) -> None:
    await create_cart(user_ids["a"], 1)
    checkout_a = await client.post(
        "/v1/billing/checkout",
        json={},
        headers=auth_headers(user_ids["a"]),
    )
    await create_cart(user_ids["b"], 1)
    checkout_b = await client.post(
        "/v1/billing/checkout",
        json={},
        headers=auth_headers(user_ids["b"]),
    )

    response = await client.get("/v1/billing/invoices", headers=auth_headers(user_ids["a"]))
    forbidden = await client.get(
        f"/v1/billing/invoices/{checkout_b.json()['invoice_id']}",
        headers=auth_headers(user_ids["a"]),
    )

    assert checkout_a.status_code == 200
    assert checkout_b.status_code == 200
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [checkout_a.json()["invoice_id"]]
    assert forbidden.status_code == 404
