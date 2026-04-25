from __future__ import annotations

import asyncio

import httpx
import respx
from app.config import Settings
from app.main import create_app
from melispy_shared import AuditLog
from sqlalchemy import select
from conftest import FakeRedis, GatewayHarness


async def test_audit_emit_records_request(
    client: httpx.AsyncClient,
    gateway_harness: GatewayHarness,
    respx_mock: respx.MockRouter,
) -> None:
    respx_mock.post("http://auth-service:8000/v1/auth/signup").mock(
        return_value=httpx.Response(202, json={"accepted": True})
    )

    response = await client.post("/v1/auth/signup")

    # Audit emit is fire-and-forget (asyncio.create_task) — yield control so the task runs.
    for _ in range(20):
        await asyncio.sleep(0.01)
        async with gateway_harness.audit_sessionmaker() as session:
            result = await session.execute(
                select(AuditLog).where(AuditLog.resource == "/v1/auth/signup")
            )
            row = result.scalar_one_or_none()
        if row is not None:
            break
    else:
        raise AssertionError("audit row not flushed within 200ms")
    assert response.status_code == 202
    assert row.event_type == "http_request"
    assert row.actor_id == "anon"
    assert row.action == "POST"
    assert row.payload["status"] == 202


async def test_audit_failure_does_not_block_request(
    settings: Settings,
    respx_mock: respx.MockRouter,
) -> None:
    app = create_app(
        settings=settings,
        redis_client=FakeRedis(),
        audit_sessionmaker=FailingSessionmaker(),  # type: ignore[arg-type]
    )
    transport = httpx.ASGITransport(app=app)
    respx_mock.post("http://auth-service:8000/v1/auth/signup").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/v1/auth/signup")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


class FailingSessionmaker:
    def __call__(self) -> FailingSessionmaker:
        return self

    async def __aenter__(self) -> object:
        raise RuntimeError("audit unavailable")

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None
