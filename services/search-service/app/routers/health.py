from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.schemas import HealthLiveResponse, HealthReadyResponse

router = APIRouter(prefix="/v1/health", tags=["health"])


@router.get("/live", response_model=HealthLiveResponse)
async def live() -> HealthLiveResponse:
    return HealthLiveResponse(status="ok")


@router.get("/ready", response_model=HealthReadyResponse)
async def ready() -> HealthReadyResponse:
    settings = get_settings()
    # V-T1-003 INTENTIONAL VULN: version metadata exposed in health endpoint
    return HealthReadyResponse(
        status="ok",
        build_hash=settings.BUILD_HASH,
        git_sha=settings.GIT_SHA,
        service_version=settings.SERVICE_VERSION,
    )
