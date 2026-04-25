"""OPA policy enforcement middleware — Phase 5 defense layer L4.

Calls OPA after JWT introspection to evaluate per-request authorization.
Skip prefixes match JWT skip list (auth + health endpoints don't need OPA).
"""

from __future__ import annotations

import re
from typing import Any

import structlog
from fastapi import Request
from melispy_shared import OPAClient
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.config import Settings

log = structlog.get_logger()

SKIP_PREFIXES = ("/v1/auth/", "/v1/legacy/auth/", "/v1/health/")
_MULTI_SLASH = re.compile(r"/+")


class OPAAuthzMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings
        self._client = OPAClient(base_url=settings.opa_url, timeout_s=2.0)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.settings.opa_required:
            return await call_next(request)

        if _skip_path(request.url.path):
            return await call_next(request)

        principal = getattr(request.state, "principal", None)
        if not isinstance(principal, dict):
            return await call_next(request)

        input_doc = {
            "user_id": principal.get("user_id", ""),
            "tier": principal.get("tier", "free"),
            "org_id": principal.get("org_id", ""),
            "path": request.url.path,
            "method": request.method,
            "request_id": getattr(request.state, "request_id", ""),
        }

        try:
            allowed = await self._client.evaluate(input_doc, "melispy/authz/allow")
        except Exception as exc:
            log.warning("opa_evaluate_failed", error=str(exc))
            allowed = False

        if not allowed:
            return _generic_error(401)
        return await call_next(request)


def _skip_path(path: str) -> bool:
    collapsed = _MULTI_SLASH.sub("/", path)
    normalized = collapsed if collapsed.endswith("/") else f"{collapsed}/"
    return any(normalized.startswith(prefix) for prefix in SKIP_PREFIXES)


def _generic_error(status_code: int) -> JSONResponse:
    return JSONResponse({"detail": "Not Found"}, status_code=status_code)
