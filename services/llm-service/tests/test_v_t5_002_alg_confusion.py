from __future__ import annotations

import base64
import hashlib
import hmac
import json
from collections.abc import Mapping

from httpx import AsyncClient
from melispy_shared import issue_jwt

from conftest import JWT_PRIVATE_KEY_PEM, JWT_PUBLIC_KEY_PEM


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _sign_hs256(payload: Mapping[str, object], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = ".".join(
        [
            _b64url(json.dumps(header, separators=(",", ":")).encode()),
            _b64url(json.dumps(payload, separators=(",", ":")).encode()),
        ]
    )
    signature = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


async def test_v_t5_002_alg_confusion_accepts_public_key_hmac(
    client: AsyncClient,
) -> None:
    payload = {"sub": "alg-confusion-user", "scope": "llm"}
    rs256_token = issue_jwt(payload, JWT_PRIVATE_KEY_PEM, alg="RS256", expires_in=900)
    assert rs256_token.count(".") == 2

    hs256_token = _sign_hs256(payload, JWT_PUBLIC_KEY_PEM)
    response = await client.post("/v1/llm/verify-token", json={"token": hs256_token})

    assert response.status_code == 200
    assert response.json()["sub"] == "alg-confusion-user"
    assert response.json()["scope"] == "llm"
