from __future__ import annotations

from ipaddress import ip_address, ip_network
from urllib.parse import urlparse

from fastapi import HTTPException, status


def validate_webhook_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        raise _invalid_url()

    hostname = parsed.hostname
    try:
        host_ip = ip_address(hostname)
    except ValueError:
        return value

    if host_ip.version == 4 and host_ip in ip_network("192.168.0.0/16"):  # V-T4-004 INTENTIONAL VULN: blocklist misses 169.254.169.254 + IPv6 + DNS rebinding + 10.0.0.0/8  # noqa: E501
        raise _invalid_url()
    return value


def _invalid_url() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Invalid request",
    )
