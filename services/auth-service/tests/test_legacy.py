from __future__ import annotations

import base64
import json

from httpx import AsyncClient


def _b64url(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _unsigned_token(kid: str) -> str:
    header = _b64url({"alg": "none", "kid": kid, "typ": "JWT"})
    payload = _b64url({"sub": "legacy-user", "email": "legacy@example.com"})
    return f"{header}.{payload}."


async def test_legacy_verify_accepts_alg_none_with_legacy_kid(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/legacy/auth/verify",
        headers={"User-Agent": "MelispyMobile/1.0"},
        json={"token": _unsigned_token("mobile-legacy-001")},
    )

    assert response.status_code == 200
    assert response.json() == {"user_id": "legacy-user", "email": "legacy@example.com"}


async def test_legacy_verify_rejects_modern_kid(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/legacy/auth/verify",
        headers={"User-Agent": "MelispyMobile/1.0"},
        json={"token": _unsigned_token("modern-001")},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not Found"}
