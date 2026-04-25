from __future__ import annotations

import secrets
import string
from datetime import UTC, datetime, timedelta
from typing import TypedDict

from app.config import get_settings


class StsCredentials(TypedDict):
    Code: str
    Type: str
    AccessKeyId: str
    SecretAccessKey: str
    Token: str
    Expiration: str
    LastUpdated: str


def _aws_access_key_suffix() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(16))


def generate_credentials() -> StsCredentials:
    settings = get_settings()
    issued_at = datetime.now(UTC).replace(microsecond=0)
    expires_at = issued_at + timedelta(seconds=settings.STS_TOKEN_TTL_S)
    return {
        "Code": "Success",
        "Type": "AWS-HMAC",
        "AccessKeyId": f"ASIA{_aws_access_key_suffix()}",
        "SecretAccessKey": secrets.token_urlsafe(40)[:40],
        "Token": secrets.token_urlsafe(150),
        "Expiration": issued_at_to_iso8601(expires_at),
        "LastUpdated": issued_at_to_iso8601(issued_at),
    }


def issued_at_to_iso8601(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
