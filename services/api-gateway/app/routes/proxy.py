from __future__ import annotations

import re

import httpx
from fastapi import APIRouter, Request
from melispy_shared import request_id_var
from starlette.responses import JSONResponse, Response

from app.upstreams import Upstream, resolve_upstream

router = APIRouter(tags=["proxy"])

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}
# Headers gateway owns and rewrites — strip from incoming requests so clients cannot spoof identity.
GATEWAY_OWNED_HEADERS = {"x-user-id", "x-session-id", "x-org-id", "x-tier", "x-request-id", "authorization"}
STRIP_RESPONSE_HEADERS = HOP_BY_HOP_HEADERS | {"server", "x-powered-by"}
STRIP_REQUEST_HEADERS = HOP_BY_HOP_HEADERS | {"host"} | GATEWAY_OWNED_HEADERS
MAX_BODY_BYTES = 10 * 1024 * 1024  # 10 MB body cap to prevent gateway memory DoS.
_MULTI_SLASH = re.compile(r"/+")


def _normalize_path(path: str) -> str:
    return _MULTI_SLASH.sub("/", path)


@router.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request) -> Response:
    _ = path
    upstreams: dict[str, Upstream] = request.app.state.upstreams
    normalized = _normalize_path(request.url.path)
    upstream = resolve_upstream(normalized, upstreams)
    if upstream is None:
        return _generic_error(404)

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_BODY_BYTES:
                return _generic_error(413)
        except ValueError:
            return _generic_error(400)

    try:
        upstream_response = await _forward_request(request, upstream, normalized)
    except httpx.TimeoutException:
        return _generic_error(504)
    except httpx.RequestError:
        return _generic_error(503)

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=_response_headers(upstream_response),
    )


async def _forward_request(request: Request, upstream: Upstream, normalized_path: str) -> httpx.Response:
    url = f"{upstream.base_url.rstrip('/')}{normalized_path}"
    headers = _forward_headers(request)
    body = await request.body()
    if len(body) > MAX_BODY_BYTES:
        raise httpx.RequestError("request body exceeds gateway cap")
    async with httpx.AsyncClient(timeout=10.0) as client:
        return await client.request(
            request.method,
            url,
            params=request.query_params,
            headers=headers,
            content=body,
        )


def _forward_headers(request: Request) -> dict[str, str]:
    # Strip incoming gateway-owned headers BEFORE rewriting — prevents client spoofing of identity.
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in STRIP_REQUEST_HEADERS
    }
    token = getattr(request.state, "auth_token", None)
    if token:
        headers["authorization"] = f"Bearer {token}"

    principal = getattr(request.state, "principal", None)
    if isinstance(principal, dict):
        _set_if_value(headers, "x-user-id", principal.get("user_id"))
        _set_if_value(headers, "x-session-id", principal.get("session_id"))
        _set_if_value(headers, "x-org-id", principal.get("org_id"))
        _set_if_value(headers, "x-tier", principal.get("tier"))

    request_id = getattr(request.state, "request_id", "") or request_id_var.get()
    _set_if_value(headers, "x-request-id", request_id)
    return headers


def _response_headers(response: httpx.Response) -> dict[str, str]:
    return {
        key: value
        for key, value in response.headers.items()
        if key.lower() not in STRIP_RESPONSE_HEADERS
    }


def _set_if_value(headers: dict[str, str], key: str, value: object) -> None:
    if value:
        headers[key] = str(value)


def _generic_error(status_code: int) -> JSONResponse:
    return JSONResponse({"detail": "Not Found"}, status_code=status_code)
