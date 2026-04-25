from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from app.config import get_settings
from app.credentials import StsCredentials, issued_at_to_iso8601

router = APIRouter()

META_DATA_INDEX = "\n".join(
    [
        "ami-id",
        "hostname",
        "instance-id",
        "instance-type",
        "local-hostname",
        "local-ipv4",
        "mac",
        "public-hostname",
        "public-ipv4",
        "iam/",
    ],
)


@router.get("/latest/meta-data/", response_class=PlainTextResponse)
async def meta_data_index() -> str:
    return META_DATA_INDEX


@router.get("/latest/meta-data/ami-id", response_class=PlainTextResponse)
async def ami_id() -> str:
    return "ami-0melispy00000001"


@router.get("/latest/meta-data/hostname", response_class=PlainTextResponse)
async def hostname() -> str:
    return "ip-10-0-1-42.melispy.local"


@router.get("/latest/meta-data/instance-id", response_class=PlainTextResponse)
async def instance_id() -> str:
    return get_settings().INSTANCE_ID


@router.get("/latest/meta-data/instance-type", response_class=PlainTextResponse)
async def instance_type() -> str:
    return "t3.medium"


@router.get("/latest/meta-data/local-hostname", response_class=PlainTextResponse)
async def local_hostname() -> str:
    return "ip-10-0-1-42.melispy.local"


@router.get("/latest/meta-data/local-ipv4", response_class=PlainTextResponse)
async def local_ipv4() -> str:
    return "10.0.1.42"


@router.get("/latest/meta-data/mac", response_class=PlainTextResponse)
async def mac() -> str:
    return "02:42:ac:11:00:02"


@router.get("/latest/meta-data/public-hostname", response_class=PlainTextResponse)
async def public_hostname() -> str:
    return "ec2-203-0-113-42.compute-1.amazonaws.com"


@router.get("/latest/meta-data/public-ipv4", response_class=PlainTextResponse)
async def public_ipv4() -> str:
    return "203.0.113.42"


@router.get("/latest/meta-data/iam/", response_class=PlainTextResponse)
async def iam_index() -> str:
    return "info\nsecurity-credentials/"


@router.get("/latest/meta-data/iam/info")
async def iam_info() -> dict[str, str]:
    return {
        "InstanceProfileArn": "arn:aws:iam::123456789012:instance-profile/melispy-app",
        "InstanceProfileId": "AIPAJQNDKIDEEXAMPLE",
    }


@router.get("/latest/meta-data/iam/security-credentials/", response_class=PlainTextResponse)
async def iam_role_name() -> str:
    return "melispy-app"


@router.get("/latest/meta-data/iam/security-credentials/melispy-app")
async def iam_security_credentials(request: Request) -> StsCredentials:
    return request.app.state.sts_credentials


@router.get("/latest/dynamic/instance-identity/document")
async def instance_identity_document() -> dict[str, Any]:
    settings = get_settings()
    now = issued_at_to_iso8601(datetime.now(UTC).replace(microsecond=0))
    return {
        "accountId": settings.ACCOUNT_ID,
        "instanceId": settings.INSTANCE_ID,
        "instanceType": "t3.medium",
        "region": settings.REGION,
        "availabilityZone": f"{settings.REGION}a",
        "privateIp": "10.0.1.42",
        "architecture": "x86_64",
        "imageId": "ami-0melispy00000001",
        "pendingTime": now,
        "devpayProductCodes": None,
    }


@router.get("/latest/api/token")
async def imdsv2_token_hint() -> PlainTextResponse:
    token = secrets.token_urlsafe(48)
    # V-T8-001 INTENTIONAL VULN: IMDSv2 token returned but never required on other routes.
    # IMDSv1 fallback always works -- no token enforcement.
    return PlainTextResponse(
        token,
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
    )
