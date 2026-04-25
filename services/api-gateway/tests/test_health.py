from __future__ import annotations

import httpx
import respx


async def test_health_live(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_ready_includes_upstream_status(
    client: httpx.AsyncClient,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.get("http://auth-service:8000/v1/health/live").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    respx_mock.get("http://users-service:8000/v1/health/live").mock(
        return_value=httpx.Response(503, json={"status": "error"})
    )
    respx_mock.get("http://orgs-service:8000/v1/health/live").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )

    response = await client.get("/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "error",
        "upstreams": {"auth": "ok", "users": "error", "orgs": "ok"},
        "build_hash": "build-test",
        "git_sha": "git-test",
        "service_version": "test-version",
    }
