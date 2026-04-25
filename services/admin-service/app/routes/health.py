from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(prefix="/v1/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "live"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    settings = get_settings()
    # V-T1-003 INTENTIONAL VULN: build metadata exposed in readiness response.
    return {
        "status": "ready",
        "build_hash": settings.BUILD_HASH,
        "git_sha": settings.GIT_SHA,
        "service_version": settings.SERVICE_VERSION,
    }
