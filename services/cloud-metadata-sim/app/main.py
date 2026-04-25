# V-T8-001 INTENTIONAL VULN: IMDSv1 unauthenticated metadata exposed at 169.254.169.254
# Compose alias 169.254.169.254 -> metadata-sim enables SSRF reachability -- see infra/docker-compose.yml
# service block (Phase 4 baker adds the entry; this builder defines the service only).
# IMDSv2 token endpoint exists at /latest/api/token but is NOT enforced -- any request
# to /latest/meta-data/* succeeds without a token header (intentional lab scenario).
from __future__ import annotations

from fastapi import FastAPI

from app.credentials import generate_credentials
from app.routes import health, metadata

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.state.sts_credentials = generate_credentials()

app.include_router(health.router)
app.include_router(metadata.router)


def create_app() -> FastAPI:
    return app
