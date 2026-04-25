from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog
from fastapi import Request
from melispy_shared import emit_audit
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

log = structlog.get_logger()


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(app)
        self.sessionmaker = sessionmaker

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            # Fire-and-forget — audit DB hangs must not delay client response.
            task = asyncio.create_task(self._emit(request, status_code, duration_ms))
            task.add_done_callback(self._on_emit_done)

    @staticmethod
    def _on_emit_done(task: asyncio.Task[None]) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            log.error("audit_emit_failed", error=str(exc))

    async def _emit(self, request: Request, status_code: int, duration_ms: int) -> None:
        principal = getattr(request.state, "principal", None)
        actor_id = "anon"
        if isinstance(principal, dict) and principal.get("user_id"):
            actor_id = principal["user_id"]
        async with self.sessionmaker() as session:
            await emit_audit(
                session,
                event_type="http_request",
                actor_id=actor_id,
                resource=request.url.path,
                action=request.method,
                payload={"status": status_code, "duration_ms": duration_ms},
            )
