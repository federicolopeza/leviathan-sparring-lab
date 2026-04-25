from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient


async def test_v_t4_002_coupon_stack_apply_3x_same_code(
    client: AsyncClient,
    auth_headers: Callable[[str, str | None, bool], dict[str, str]],
    create_cart: Callable[[str, int], object],
    create_coupon: Callable[[str, int | None, int | None], object],
) -> None:
    await create_cart("stack-user", 1)
    await create_coupon("SAVE10", 10, None)
    headers = auth_headers("stack-user")

    response = None
    for _ in range(3):
        response = await client.post(
            "/v1/billing/cart/coupon",
            json={"coupon_code": "SAVE10"},
            headers=headers,
        )

    assert response is not None
    assert response.status_code == 200
    assert len(response.json()["coupons"]) == 3
    assert response.json()["discount_cents"] == 270
