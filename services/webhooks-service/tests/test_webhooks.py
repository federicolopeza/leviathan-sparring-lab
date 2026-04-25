from __future__ import annotations

import json

import httpx
import respx
from app.deps.db import SessionLocal
from app.services.queue import webhook_queue
from httpx import AsyncClient


async def _create_webhook(
    client: AsyncClient,
    auth_headers: object,
    *,
    url: str = "https://receiver.example/hook",
    user_key: str = "owner",
    events: list[str] | None = None,
) -> dict[str, object]:
    headers = auth_headers(user_key)
    response = await client.post(
        "/v1/webhooks",
        json={"url": url, "events": events or ["invoice.created"]},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


async def test_create_webhook_succeeds_with_https_url(
    client: AsyncClient,
    auth_headers: object,
) -> None:
    body = await _create_webhook(client, auth_headers)

    assert body["url"] == "https://receiver.example/hook"
    assert body["events"] == ["invoice.created"]
    assert body["secret"]


async def test_create_webhook_rejects_192_168(
    client: AsyncClient,
    auth_headers: object,
) -> None:
    response = await client.post(
        "/v1/webhooks",
        json={"url": "http://192.168.1.10/hook", "events": ["invoice.created"]},
        headers=auth_headers("owner"),
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request"}


async def test_v_t4_004_ssrf_169_254_metadata_accepted(
    client: AsyncClient,
    auth_headers: object,
) -> None:
    response = await client.post(
        "/v1/webhooks",
        json={"url": "http://169.254.169.254/latest/meta-data", "events": ["invoice.created"]},
        headers=auth_headers("owner"),
    )

    assert response.status_code == 201


async def test_v_t4_004_ssrf_ipv6_loopback_accepted(
    client: AsyncClient,
    auth_headers: object,
) -> None:
    response = await client.post(
        "/v1/webhooks",
        json={"url": "http://[::1]/hook", "events": ["invoice.created"]},
        headers=auth_headers("owner"),
    )

    assert response.status_code == 201


async def test_v_t4_004_ssrf_10_0_0_1_accepted(
    client: AsyncClient,
    auth_headers: object,
) -> None:
    response = await client.post(
        "/v1/webhooks",
        json={"url": "http://10.0.0.1/hook", "events": ["invoice.created"]},
        headers=auth_headers("owner"),
    )

    assert response.status_code == 201


async def test_list_webhooks_only_own(client: AsyncClient, auth_headers: object) -> None:
    owner_webhook = await _create_webhook(client, auth_headers, user_key="owner")
    await _create_webhook(
        client,
        auth_headers,
        url="https://other.example/hook",
        user_key="other",
    )

    response = await client.get("/v1/webhooks", headers=auth_headers("owner"))

    assert response.status_code == 200
    assert [item["webhook_id"] for item in response.json()] == [owner_webhook["webhook_id"]]


@respx.mock
async def test_test_webhook_sends_request(client: AsyncClient, auth_headers: object) -> None:
    webhook = await _create_webhook(client, auth_headers)
    route = respx.post("https://receiver.example/hook").mock(
        return_value=httpx.Response(202, text="accepted")
    )

    response = await client.post(
        f"/v1/webhooks/{webhook['webhook_id']}/test",
        headers=auth_headers("owner"),
    )

    assert response.status_code == 200
    assert response.json()["status_code"] == 202
    assert response.json()["body_preview"] == "accepted"
    assert route.called
    assert "x-melispy-signature" in route.calls[0].request.headers


@respx.mock
async def test_v_t4_010_retry_delivers_duplicate_with_different_event_ids(
    client: AsyncClient,
    auth_headers: object,
    user_ids: dict[str, str],
) -> None:
    await _create_webhook(client, auth_headers)
    route = respx.post("https://receiver.example/hook").mock(
        side_effect=[
            httpx.Response(500, text="flap"),
            httpx.Response(200, text="ok"),
        ]
    )
    response = await client.post(
        "/v1/webhooks/_internal/dispatch",
        json={
            "event_type": "invoice.created",
            "payload": {"invoice_id": "inv_123"},
            "target_user_id": user_ids["owner"],
        },
        headers=auth_headers("admin"),
    )
    assert response.status_code == 200
    assert response.json()["enqueued"] == 1

    async with SessionLocal() as db:
        processed = await webhook_queue.drain(db, force=True)

    assert len(processed) == 2
    assert route.call_count == 2
    event_ids = [
        json.loads(call.request.content.decode())["event_id"]
        for call in route.calls
    ]
    assert event_ids[0] != event_ids[1]


async def test_health_ready_leaks_build(client: AsyncClient) -> None:
    response = await client.get("/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "build_hash": "test-build",
        "git_sha": "test-sha",
        "service_version": "test-version",
    }
