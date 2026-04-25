from __future__ import annotations

import base64
import json

from httpx import AsyncClient
from pytest import MonkeyPatch


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _unsigned_rs256_token_with_kid(kid: str) -> str:
    header = {"alg": "RS256", "typ": "JWT", "kid": kid}
    payload = {"sub": "kid-traversal-user"}
    return ".".join(
        [
            _b64url(json.dumps(header, separators=(",", ":")).encode()),
            _b64url(json.dumps(payload, separators=(",", ":")).encode()),
            _b64url(b"signature"),
        ]
    )


async def test_v_t5_003_kid_traversal_attempts_unsanitized_key_path(
    client: AsyncClient,
    monkeypatch: MonkeyPatch,
) -> None:
    opened_paths: list[str] = []

    def fake_open(path: str, mode: str) -> object:
        opened_paths.append(path)
        raise FileNotFoundError(path)

    monkeypatch.setattr("builtins.open", fake_open)
    token = _unsigned_rs256_token_with_kid("../../etc/passwd")

    response = await client.post("/v1/llm/verify-kid", json={"token": token})

    assert response.status_code == 200
    assert opened_paths == ["/keys/../../etc/passwd.pub"]
    assert response.json()["error"] == "FileNotFoundError"
