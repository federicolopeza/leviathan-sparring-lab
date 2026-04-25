from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from melispy_shared import RequestIdMiddleware, configure_logging
from redis.asyncio import from_url as redis_from_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.deps.db import create_audit_sessionmaker
from app.middleware.audit import AuditMiddleware
from app.middleware.jwt_introspect import JWTIntrospectMiddleware
from app.middleware.opa_authz import OPAAuthzMiddleware
from app.middleware.tier_rate_limit import TierRateLimitMiddleware
from app.routes.health import router as health_router
from app.routes.proxy import router as proxy_router
from app.upstreams import UPSTREAM_REGISTRY, build_upstream_registry


def create_app(
    settings: Settings | None = None,
    redis_client: Any | None = None,
    audit_sessionmaker: async_sessionmaker[AsyncSession] | None = None,
) -> FastAPI:
    configure_logging()
    resolved_settings = settings or Settings()
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = resolved_settings
    upstreams = build_upstream_registry(resolved_settings)
    UPSTREAM_REGISTRY.clear()
    UPSTREAM_REGISTRY.update(upstreams)
    app.state.upstreams = upstreams

    redis = redis_client or redis_from_url(resolved_settings.redis_url, decode_responses=True)
    audit_sessions = audit_sessionmaker or create_audit_sessionmaker(resolved_settings)

    app.include_router(health_router)
    app.include_router(proxy_router)

    app.add_middleware(AuditMiddleware, sessionmaker=audit_sessions)
    app.add_middleware(OPAAuthzMiddleware, settings=resolved_settings)
    app.add_middleware(TierRateLimitMiddleware, settings=resolved_settings, redis_client=redis)
    app.add_middleware(JWTIntrospectMiddleware, settings=resolved_settings)
    app.add_middleware(RequestIdMiddleware)
    return app


app = create_app()
