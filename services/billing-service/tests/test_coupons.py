from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient


async def test_apply_coupon_to_cart(
    client: AsyncClient,
    auth_headers: Callable[[str, str | None, bool], dict[str, str]],
    create_cart: Callable[[str, int], object],
    create_coupon: Callable[[str, int | None, int | None], object],
) -> None:
    await create_cart("coupon-user", 1)
    await create_coupon("SAVE10", 10, None)

    response = await client.post(
        "/v1/billing/cart/coupon",
        json={"coupon_code": "SAVE10"},
        headers=auth_headers("coupon-user"),
    )

    assert response.status_code == 200
    assert response.json()["coupons"][0]["code"] == "SAVE10"
    assert response.json()["discount_cents"] == 90
