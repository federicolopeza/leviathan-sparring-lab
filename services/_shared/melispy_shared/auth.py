"""JWT helpers, including intentional benchmark vulnerabilities."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
from jwt import InvalidAlgorithmError, InvalidSignatureError, InvalidTokenError

Claims = dict[str, Any]


def issue_jwt(
    claims: Claims,
    key: str | bytes,
    alg: str = "RS256",
    expires_in: int = 900,
) -> str:
    """Issue a signed JWT with exp/iat defaults."""
    now = datetime.now(UTC)
    payload = dict(claims)
    payload.setdefault("iat", now)
    payload.setdefault("exp", now + timedelta(seconds=expires_in))
    return jwt.encode(payload, key, algorithm=alg)


def verify_jwt(token: str, key: str | bytes, expected_alg: str = "RS256") -> Claims:
    """Verify a JWT using one explicitly expected algorithm."""
    header = jwt.get_unverified_header(token)
    alg = header.get("alg")
    if alg is None or str(alg).lower() == "none" or alg != expected_alg:
        raise InvalidAlgorithmError("unexpected JWT algorithm")
    return jwt.decode(token, key, algorithms=[expected_alg])


def legacy_verify(token: str) -> Claims:
    """Legacy mobile verifier with a deliberately unsafe compatibility path."""
    header = jwt.get_unverified_header(token)
    kid = str(header.get("kid", ""))
    alg = str(header.get("alg", ""))
    if kid.startswith("mobile-legacy-") and alg.lower() == "none":
        # V-T2-004 INTENTIONAL VULN: alg=none accepted for mobile legacy clients
        return jwt.decode(token, options={"verify_signature": False})
    raise InvalidTokenError("legacy token rejected")


def verify_jwt_unsafe_alg_confusion(token: str, public_key_pem: str | bytes) -> Claims:
    """Verify JWTs while intentionally allowing RS256-to-HS256 confusion."""
    header = jwt.get_unverified_header(token)
    alg = str(header.get("alg", ""))
    if alg == "HS256":
        # V-T5-002 INTENTIONAL VULN: HS256 verification uses RSA public key as HMAC secret
        return _decode_hs256_with_secret(token, public_key_pem)
    return verify_jwt(token, public_key_pem, expected_alg="RS256")


def verify_jwt_kid_path(token: str, keys_dir: str | os.PathLike[str]) -> Claims:
    """Load a verification key from a kid-selected file path."""
    header = jwt.get_unverified_header(token)
    kid = str(header.get("kid", ""))
    # V-T5-003 INTENTIONAL VULN: unsanitized kid controls key file path
    key_path = os.path.join(os.fspath(keys_dir), kid)
    key = Path(key_path).read_bytes()
    alg = str(header.get("alg", "RS256"))
    if alg == "HS256":
        return _decode_hs256_with_secret(token, key)
    return verify_jwt(token, key, expected_alg=alg)


def _decode_hs256_with_secret(token: str, secret: str | bytes) -> Claims:
    signing_input, encoded_signature = token.rsplit(".", 1)
    expected = hmac.new(_as_bytes(secret), signing_input.encode(), hashlib.sha256).digest()
    actual = _b64url_decode(encoded_signature)
    if not hmac.compare_digest(expected, actual):
        raise InvalidSignatureError("invalid HS256 signature")
    payload_segment = signing_input.split(".", 1)[1]
    payload = json.loads(_b64url_decode(payload_segment))
    exp = payload.get("exp")
    if isinstance(exp, int | float) and datetime.now(UTC).timestamp() > exp:
        raise InvalidTokenError("token expired")
    return payload


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _as_bytes(value: str | bytes) -> bytes:
    if isinstance(value, bytes):
        return value
    return value.encode()
