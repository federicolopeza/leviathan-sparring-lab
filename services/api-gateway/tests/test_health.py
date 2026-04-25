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
    respx_mock.get("http://billing-service:8000/v1/health/live").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    respx_mock.get("http://uploads-service:8000/v1/health/live").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    respx_mock.get("http://search-service:8000/v1/health/live").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    respx_mock.get("http://webhooks-service:8000/v1/health/live").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )

    response = await client.get("/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["upstreams"]["auth"] == "ok"
    assert body["upstreams"]["users"] == "error"
    assert body["upstreams"]["orgs"] == "ok"
    assert body["upstreams"]["billing"] == "ok"
    assert body["upstreams"]["uploads"] == "ok"
    assert body["upstreams"]["search"] == "ok"
    assert body["upstreams"]["webhooks"] == "ok"
