from __future__ import annotations

from collections.abc import Callable

import httpx
import respx


async def test_proxy_unauth_forwarded_to_auth_signup(
    client: httpx.AsyncClient,
    respx_mock: respx.MockRouter,
) -> None:
    route = respx_mock.post("http://auth-service:8000/v1/auth/signup").mock(
        return_value=httpx.Response(201, json={"id": "user-1"})
    )

    response = await client.post("/v1/auth/signup", json={"email": "a@example.test"})

    assert response.status_code == 201
    assert response.json() == {"id": "user-1"}
    assert route.called
    assert "authorization" not in route.calls.last.request.headers


async def test_proxy_users_requires_bearer_token(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/users/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not Found"}


async def test_proxy_users_with_valid_jwt_forwards(
    client: httpx.AsyncClient,
    respx_mock: respx.MockRouter,
    token_factory: Callable[..., str],
) -> None:
    token = token_factory(user_id="user-123")
    route = respx_mock.get("http://users-service:8000/v1/users/me").mock(
        return_value=httpx.Response(200, json={"id": "user-123"})
    )

    response = await client.get("/v1/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"id": "user-123"}
    assert route.calls.last.request.headers["x-user-id"] == "user-123"
    assert route.calls.last.request.headers["x-session-id"] == "session-1"
    assert route.calls.last.request.headers["x-org-id"] == "org-1"
    assert route.calls.last.request.headers["x-tier"] == "free"


async def test_proxy_invalid_jwt_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/users/me", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Not Found"}


async def test_proxy_unknown_path_returns_uniform_401(client: httpx.AsyncClient) -> None:
    # Anti-enumeration: invalid JWT and unknown path return SAME status+body to avoid
    # 401 vs 404 oracle (MASTER-PROMPT Section 12 anti-pattern).
    response = await client.get("/v1/nope")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not Found"}


async def test_proxy_upstream_timeout_returns_504(
    client: httpx.AsyncClient,
    respx_mock: respx.MockRouter,
) -> None:
    request = httpx.Request("POST", "http://auth-service:8000/v1/auth/signup")
    respx_mock.post("http://auth-service:8000/v1/auth/signup").mock(
        side_effect=httpx.TimeoutException("timeout", request=request)
    )

    response = await client.post("/v1/auth/signup", json={"email": "a@example.test"})

    assert response.status_code == 504
    assert response.json() == {"detail": "Not Found"}


async def test_proxy_upstream_5xx_passthrough(
    client: httpx.AsyncClient,
    respx_mock: respx.MockRouter,
    token_factory: Callable[..., str],
) -> None:
    token = token_factory()
    respx_mock.get("http://users-service:8000/v1/users/me").mock(
        return_value=httpx.Response(500, json={"detail": "upstream failed"})
    )

    response = await client.get("/v1/users/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 500
    assert response.json() == {"detail": "upstream failed"}
