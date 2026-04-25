from __future__ import annotations

import base64
import hashlib
import hmac
import json
import shutil
from pathlib import Path
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import InvalidAlgorithmError
from melispy_shared.auth import (
    issue_jwt,
    legacy_verify,
    verify_jwt,
    verify_jwt_kid_path,
    verify_jwt_unsafe_alg_confusion,
)


@pytest.fixture
def rsa_keys() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


def test_issue_verify_roundtrip(rsa_keys: tuple[str, str]) -> None:
    private_pem, public_pem = rsa_keys
    token = issue_jwt({"sub": "user-1", "role": "admin"}, private_pem)

    claims = verify_jwt(token, public_pem)

    assert claims["sub"] == "user-1"
    assert claims["role"] == "admin"


def test_verify_rejects_alg_none(rsa_keys: tuple[str, str]) -> None:
    _, public_pem = rsa_keys
    token = jwt.encode({"sub": "user-1"}, key="", algorithm="none")

    with pytest.raises(InvalidAlgorithmError):
        verify_jwt(token, public_pem)


def test_legacy_verify_accepts_alg_none_with_legacy_kid() -> None:
    token = jwt.encode(
        {"sub": "legacy-user"},
        key="",
        algorithm="none",
        headers={"kid": "mobile-legacy-ios-1"},
    )

    claims = legacy_verify(token)

    assert claims["sub"] == "legacy-user"


def test_unsafe_alg_confusion_rs_to_hs(rsa_keys: tuple[str, str]) -> None:
    _, public_pem = rsa_keys
    token = _encode_hs256({"sub": "confused"}, public_pem, {"alg": "HS256", "typ": "JWT"})

    claims = verify_jwt_unsafe_alg_confusion(token, public_pem)

    assert claims["sub"] == "confused"


def test_kid_path_traversal(tmp_path: Path) -> None:
    claims = _run_kid_path_traversal(tmp_path)
    assert claims["sub"] == "kid-traversal"


def _run_kid_path_traversal(tmp_path: Path) -> dict[str, object]:
    keys_dir = tmp_path / "base" / "keys"
    traversed_dir = tmp_path / "etc"
    keys_dir.mkdir(parents=True)
    traversed_dir.mkdir()
    secret = b"attacker-controlled-secret"
    (traversed_dir / "passwd").write_bytes(secret)
    token = _encode_hs256(
        {"sub": "kid-traversal"},
        secret,
        {"alg": "HS256", "typ": "JWT", "kid": "../../etc/passwd"},
    )

    claims = verify_jwt_kid_path(token, keys_dir)

    return claims


def _encode_hs256(
    payload: dict[str, object],
    secret: str | bytes,
    header: dict[str, object],
) -> str:
    signing_input = ".".join([_b64url_json(header), _b64url_json(payload)])
    secret_bytes = secret.encode() if isinstance(secret, str) else secret
    signature = hmac.new(secret_bytes, signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


def _b64url_json(value: dict[str, object]) -> str:
    return _b64url(json.dumps(value, separators=(",", ":"), sort_keys=True).encode())


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()
