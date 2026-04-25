from __future__ import annotations

import httpx
from fastapi import APIRouter, Request

from app.config import Settings
from app.upstreams import Upstream

router = APIRouter(prefix="/v1/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request) -> dict[str, object]:
    settings: Settings = request.app.state.settings
    upstreams: dict[str, Upstream] = request.app.state.upstreams
    upstream_status = await _check_upstreams(upstreams)
    status = "ok" if all(value == "ok" for value in upstream_status.values()) else "error"
    return {
        "status": status,
        "upstreams": upstream_status,
        # VULN: V-T1-003 INTENTIONAL — health/ready leaks build info.
        "build_hash": settings.build_hash,
        "git_sha": settings.git_sha,
        "service_version": settings.service_version,
    }


async def _check_upstreams(upstreams: dict[str, Upstream]) -> dict[str, str]:
    # Iterate registered upstreams directly — registry-driven, no KeyError on misconfig.
    result: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, upstream in upstreams.items():
            try:
                response = await client.get(f"{upstream.base_url.rstrip('/')}/v1/health/live")
            except httpx.HTTPError:
                result[name] = "error"
            else:
                result[name] = "ok" if response.status_code < 500 else "error"
    return result
