from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class Upstream:
    name: str
    base_url: str
    requires_jwt: bool
    prefixes: tuple[str, ...]


def build_upstream_registry(settings: Settings) -> dict[str, Upstream]:
    return {
        "auth": Upstream(
            name="auth",
            base_url=settings.auth_service_url,
            requires_jwt=False,
            prefixes=("/v1/auth/", "/v1/legacy/auth/"),
        ),
        "users": Upstream(
            name="users",
            base_url=settings.users_service_url,
            requires_jwt=True,
            prefixes=("/v1/users/",),
        ),
        "orgs": Upstream(
            name="orgs",
            base_url=settings.orgs_service_url,
            requires_jwt=True,
            prefixes=("/v1/orgs/",),
        ),
        "billing": Upstream(
            name="billing",
            base_url=settings.billing_service_url,
            requires_jwt=True,
            prefixes=("/v1/billing/",),
        ),
        "uploads": Upstream(
            name="uploads",
            base_url=settings.uploads_service_url,
            requires_jwt=True,
            prefixes=("/v1/uploads/",),
        ),
        "search": Upstream(
            name="search",
            base_url=settings.search_service_url,
            requires_jwt=True,
            prefixes=("/v1/search/",),
        ),
        "webhooks": Upstream(
            name="webhooks",
            base_url=settings.webhooks_service_url,
            requires_jwt=True,
            prefixes=("/v1/webhooks/",),
        ),
        "agents": Upstream(
            name="agents",
            base_url=settings.agents_service_url,
            requires_jwt=True,
            prefixes=("/v1/agents/",),
        ),
        "llm": Upstream(
            name="llm",
            base_url=settings.llm_service_url,
            requires_jwt=True,
            prefixes=("/v1/llm/",),
        ),
    }


UPSTREAM_REGISTRY: dict[str, Upstream] = {}


def resolve_upstream(path: str, registry: dict[str, Upstream]) -> Upstream | None:
    normalized = path if path.endswith("/") else f"{path}/"
    for upstream in registry.values():
        if any(normalized.startswith(prefix) for prefix in upstream.prefixes):
            return upstream
    return None
