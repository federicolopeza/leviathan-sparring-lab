from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient


async def test_checkout_completes_pending_cart(
    client: AsyncClient,
    auth_headers: Callable[[str, str | None, bool], dict[str, str]],
    create_cart: Callable[[str, int], object],
) -> None:
    await create_cart("checkout-user", 1)

    response = await client.post(
        "/v1/billing/checkout",
        json={"idempotency_key": "checkout-once"},
        headers=auth_headers("checkout-user"),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


async def test_checkout_creates_invoice_with_correct_total(
    client: AsyncClient,
    auth_headers: Callable[[str, str | None, bool], dict[str, str]],
    create_cart: Callable[[str, int], object],
) -> None:
    await create_cart("invoice-total-user", 2)

    response = await client.post(
        "/v1/billing/checkout",
        json={},
        headers=auth_headers("invoice-total-user"),
    )
    invoice = await client.get(
        f"/v1/billing/invoices/{response.json()['invoice_id']}",
        headers=auth_headers("invoice-total-user"),
    )

    assert response.status_code == 200
    assert invoice.status_code == 200
    assert invoice.json()["total_cents"] == 1800
