from __future__ import annotations

import re
from typing import Any

from fastapi import Request
from jwt import InvalidTokenError
from melispy_shared import request_id_var, verify_jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.config import Settings

SKIP_PREFIXES = ("/v1/auth/", "/v1/legacy/auth/", "/v1/health/")
_MULTI_SLASH = re.compile(r"/+")


class JWTIntrospectMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.request_id = request_id_var.get() or request.headers.get("x-request-id", "")
        if _skip_path(request.url.path):
            request.state.principal = None
            return await call_next(request)

        token = _bearer_token(request.headers.get("authorization"))
        if token is None:
            return _generic_error(401)

        try:
            claims = verify_jwt(token, self.settings.jwt_public_key_pem, expected_alg="RS256")
        except (InvalidTokenError, ValueError, TypeError):
            return _generic_error(401)

        request.state.auth_token = token
        request.state.principal = _principal_from_claims(claims)
        return await call_next(request)


def _skip_path(path: str) -> bool:
    # Collapse double slashes before prefix-match — prevents `//v1/auth/...` JWT bypass.
    collapsed = _MULTI_SLASH.sub("/", path)
    normalized = collapsed if collapsed.endswith("/") else f"{collapsed}/"
    return any(normalized.startswith(prefix) for prefix in SKIP_PREFIXES)


def _bearer_token(value: str | None) -> str | None:
    if value is None:
        return None
    scheme, _, token = value.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def _principal_from_claims(claims: dict[str, Any]) -> dict[str, str]:
    user_id = str(claims.get("user_id") or claims.get("sub") or "")
    principal = {
        "user_id": user_id,
        "session_id": str(claims.get("session_id") or claims.get("sid") or ""),
        "email": str(claims.get("email") or ""),
        "org_id": str(claims.get("org_id") or ""),
        "tier": str(claims.get("tier") or "free"),
    }
    return principal


def _generic_error(status_code: int) -> JSONResponse:
    return JSONResponse({"detail": "Not Found"}, status_code=status_code)
