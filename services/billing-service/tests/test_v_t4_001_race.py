from __future__ import annotations

import asyncio
from collections.abc import Callable

from httpx import AsyncClient


async def test_v_t4_001_race_double_charge_concurrent(
    client: AsyncClient,
    auth_headers: Callable[[str, str | None, bool], dict[str, str]],
    create_cart: Callable[[str, int], object],
) -> None:
    await create_cart("race-user", 1)
    headers = auth_headers("race-user")

    first, second = await asyncio.gather(
        client.post("/v1/billing/checkout", json={"idempotency_key": "same"}, headers=headers),
        client.post("/v1/billing/checkout", json={"idempotency_key": "same"}, headers=headers),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["invoice_id"] != second.json()["invoice_id"]
