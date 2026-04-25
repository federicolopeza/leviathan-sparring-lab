from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(prefix="/v1/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    settings = get_settings()
    # V-T1-003 INTENTIONAL VULN: build info leakage
    return {
        "status": "ok",
        "build_hash": settings.BUILD_HASH,
        "git_sha": settings.GIT_SHA,
        "service_version": settings.SERVICE_VERSION,
    }
