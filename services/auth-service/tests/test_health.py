from __future__ import annotations

from httpx import AsyncClient


async def test_health_live_minimal(client: AsyncClient) -> None:
    response = await client.get("/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_ready_leaks_build_info(client: AsyncClient) -> None:
    response = await client.get("/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "build_hash": "test-build",
        "git_sha": "test-sha",
        "service_version": "test-version",
    }
