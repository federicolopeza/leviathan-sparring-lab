from __future__ import annotations

import httpx
import respx


async def test_jwt_introspect_rejects_missing_bearer(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/orgs/current")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not Found"}


async def test_jwt_introspect_allows_auth_routes_without_token(
    client: httpx.AsyncClient,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("http://auth-service:8000/v1/legacy/auth/login").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    response = await client.post("/v1/legacy/auth/login", json={"email": "a@example.test"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
