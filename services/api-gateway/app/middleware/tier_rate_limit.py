from __future__ import annotations

from typing import Any

from fastapi import Request
from melispy_shared import check_rate_limit
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.config import Settings

PERIOD_S = 60


class TierRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, settings: Settings, redis_client: Any) -> None:
        super().__init__(app)
        self.settings = settings
        self.redis = redis_client

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        principal = getattr(request.state, "principal", None)
        tier = _tier(principal)
        limit = self.settings.tier_limits().get(tier, self.settings.tier_rate_limit_free)
        key = _rate_limit_key(request, principal, tier)
        allowed, remaining = await check_rate_limit(self.redis, key, limit, PERIOD_S)
        request.state.rate_limit_remaining = remaining

        if not allowed:
            return JSONResponse(
                {"detail": "rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": str(PERIOD_S), "X-RateLimit-Remaining": "0"},
            )
        return await call_next(request)


def _tier(principal: dict[str, str] | None) -> str:
    if principal is None:
        return "free"
    return principal.get("tier") or "free"


def _rate_limit_key(request: Request, principal: dict[str, str] | None, tier: str) -> str:
    if principal is not None and principal.get("user_id"):
        return f"tier-rate:{tier}:user:{principal['user_id']}"
    return f"tier-rate:{tier}:ip:{_client_ip(request)}"


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"
