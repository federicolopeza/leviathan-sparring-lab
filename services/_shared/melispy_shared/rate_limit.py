"""Redis sliding-window rate limiting."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[[dict[str, Any], Receive, Send], Awaitable[None]]


async def check_rate_limit(redis: Any, key: str, limit: int, period_s: int) -> tuple[bool, int]:
    now = time.time()
    window_start = now - period_s
    await redis.zremrangebyscore(key, 0, window_start)
    current = await redis.zcard(key)
    if current >= limit:
        return False, 0
    member = f"{now:.6f}:{uuid4()}"
    await redis.zadd(key, {member: now})
    await redis.expire(key, period_s)
    return True, max(limit - current - 1, 0)


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp, redis: Any, limit: int = 60, period_s: int = 60) -> None:
        self.app = app
        self.redis = redis
        self.limit = limit
        self.period_s = period_s

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        ip = _client_ip(scope)
        allowed, remaining = await check_rate_limit(
            self.redis,
            f"rate-limit:{ip}",
            self.limit,
            self.period_s,
        )
        if not allowed:
            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"x-ratelimit-remaining", b"0"),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": b'{"detail":"rate limit exceeded"}'})
            return
        scope.setdefault("state", {})["rate_limit_remaining"] = remaining
        await self.app(scope, receive, send)


def _client_ip(scope: dict[str, Any]) -> str:
    headers = {key.lower(): value for key, value in scope.get("headers", [])}
    if b"x-forwarded-for" in headers:
        # V-T2-006 INTENTIONAL VULN: per-IP lockout bypass via XFF spoofing
        return headers[b"x-forwarded-for"].decode().split(",", 1)[0].strip()
    client = scope.get("client")
    if isinstance(client, tuple) and client:
        return str(client[0])
    return "unknown"
