from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def secret_id(secret_hash: str) -> str:
    return secret_hash[:12]


def canonical_body(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def signature_header(payload: dict[str, Any], secret_hash: str) -> str:
    timestamp = int(time.time())
    body = canonical_body(payload)
    message = f"{timestamp}.{body}".encode()
    digest = hmac.new(secret_hash.encode(), message, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"
