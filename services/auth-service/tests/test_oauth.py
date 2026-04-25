from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_oauth_start_returns_state_and_url(client: AsyncClient) -> None:
    resp = await client.get("/v1/auth/oauth/google/start", params={"redirect": "/dashboard"})
    assert resp.status_code == 200
    body = resp.json()
    assert "state" in body and body["state"]
    assert "auth_url" in body and "accounts.google.com" in body["auth_url"]


@pytest.mark.asyncio
async def test_oauth_callback_stub_issues_tokens(client: AsyncClient) -> None:
    start = await client.get("/v1/auth/oauth/google/start")
    state = start.json()["state"]

    resp = await client.get("/v1/auth/oauth/google/callback", params={"state": state, "code": "stub"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body and body["access_token"]
    assert "refresh_token" in body and body["refresh_token"]


@pytest.mark.asyncio
async def test_oauth_state_csrf_replays_across_browsers(client: AsyncClient) -> None:
    """V-T2-003 reproducer: state from browser-A works in browser-B (not session-bound)."""
    start = await client.get("/v1/auth/oauth/google/start", params={"redirect": "/dashboard"})
    state_from_browser_a = start.json()["state"]

    # Simulating browser-B submitting browser-A's state — should succeed (vuln present)
    resp_browser_b = await client.get(
        "/v1/auth/oauth/google/callback",
        params={"state": state_from_browser_a, "code": "browser-b-code"},
    )
    assert resp_browser_b.status_code == 200, (
        f"V-T2-003: state CSRF not exploitable — got {resp_browser_b.status_code}"
    )
    assert "access_token" in resp_browser_b.json()


@pytest.mark.asyncio
async def test_oauth_unknown_provider_returns_404(client: AsyncClient) -> None:
    resp = await client.get("/v1/auth/oauth/facebook/start")
    assert resp.status_code == 404
