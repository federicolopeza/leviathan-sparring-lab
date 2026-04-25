from __future__ import annotations

from collections import defaultdict
from time import time

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from melispy_shared import RateLimitMiddleware, RequestIdMiddleware, configure_logging

from app.routes import auth, health, legacy, magic, oauth, sessions


class InMemoryRateLimitStore:
    def __init__(self) -> None:
        self._buckets: dict[str, dict[str, float]] = defaultdict(dict)

    async def zremrangebyscore(self, key: str, minimum: float, maximum: float) -> None:
        bucket = self._buckets[key]
        for member, score in list(bucket.items()):
            if minimum <= score <= maximum:
                del bucket[member]

    async def zcard(self, key: str) -> int:
        return len(self._buckets[key])

    async def zadd(self, key: str, mapping: dict[str, float]) -> None:
        self._buckets[key].update(mapping)

    async def expire(self, key: str, period_s: int) -> None:
        cutoff = time() - period_s
        await self.zremrangebyscore(key, 0, cutoff)


configure_logging()

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.melispy.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
_rate_store = InMemoryRateLimitStore()  # module-level for test reset access
app.add_middleware(RateLimitMiddleware, redis=_rate_store, limit=25, period_s=10)
app.add_middleware(RequestIdMiddleware)

app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(legacy.router)
app.include_router(magic.router)
app.include_router(oauth.router)
app.include_router(health.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code in {status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND}:
        return JSONResponse(status_code=exc.status_code, content={"detail": "Not Found"})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request,
    _exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )


def create_app() -> FastAPI:
    return app
