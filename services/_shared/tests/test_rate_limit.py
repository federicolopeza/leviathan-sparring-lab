from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from melispy_shared.rate_limit import RateLimitMiddleware

from tests.conftest import FakeRedis


async def test_xff_spoof_bypasses_lockout(fake_redis: FakeRedis) -> None:
    app = RateLimitMiddleware(_ok_app, fake_redis, limit=2, period_s=60)

    assert await _request(app, "198.51.100.10") == 200
    assert await _request(app, "198.51.100.10") == 200
    assert await _request(app, "198.51.100.10") == 429
    assert await _request(app, "203.0.113.55") == 200


async def _ok_app(
    scope: dict[str, Any],
    receive: Callable[[], Awaitable[dict[str, Any]]],
    send: Callable[[dict[str, Any]], Awaitable[None]],
) -> None:
    _ = scope, receive
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


async def _request(app: RateLimitMiddleware, xff: str) -> int:
    messages: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    await app(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"x-forwarded-for", xff.encode())],
            "client": ("10.0.0.1", 12345),
        },
        receive,
        send,
    )
    start = next(message for message in messages if message["type"] == "http.response.start")
    return int(start["status"])
