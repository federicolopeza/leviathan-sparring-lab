from __future__ import annotations

from collections.abc import Callable

import httpx
import respx


async def test_tier_rate_limit_free_blocked_after_quota(
    client: httpx.AsyncClient,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("http://auth-service:8000/v1/auth/signup").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    assert (await client.post("/v1/auth/signup")).status_code == 200
    assert (await client.post("/v1/auth/signup")).status_code == 200
    response = await client.post("/v1/auth/signup")

    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"


async def test_tier_rate_limit_pro_higher_quota(
    client: httpx.AsyncClient,
    respx_mock: respx.MockRouter,
    token_factory: Callable[..., str],
) -> None:
    token = token_factory(user_id="pro-user", tier="pro")
    respx_mock.get("http://users-service:8000/v1/users/me").mock(
        return_value=httpx.Response(200, json={"id": "pro-user"})
    )
    headers = {"Authorization": f"Bearer {token}"}

    statuses = [(await client.get("/v1/users/me", headers=headers)).status_code for _ in range(4)]
    blocked = await client.get("/v1/users/me", headers=headers)

    assert statuses == [200, 200, 200, 200]
    assert blocked.status_code == 429
