# Melispy Auth Service

FastAPI authentication service for Melispy v3. The service exposes signup, email
verification, password login, password reset, refresh, logout, session management,
legacy mobile verification, and health endpoints.

## Local test

```bash
uv run pytest tests/ -v
```

The test suite uses SQLite through `sqlite+aiosqlite:///./test.db` and creates the
SQLAlchemy metadata directly. Do not run Alembic against a real Postgres database
from this test path.

## Runtime

- API docs are disabled with `docs_url=None`, `redoc_url=None`, and `openapi_url=None`.
- JWTs are RS256. If PEM keys are not provided by environment, the process creates
  an ephemeral keypair for local/test startup.
- `melispy_session` is an HTTP-only cookie.
- JSON logging and request IDs come from `melispy_shared`.

## Threat model

This service intentionally includes benchmark vulnerabilities for Phase 0. Phase 1
adds the broader V-T2-001..006 auth weakness set.

- V-T2-004: legacy mobile auth accepts `alg=none` JWTs when `kid` starts with
  `mobile-legacy-*`. Entry point and call site: `app/routes/legacy.py:18` and
  `app/routes/legacy.py:26`.
- V-T1-003: readiness leaks build metadata. Reproducer route:
  `app/routes/health.py:18`.
- V-T3-005: cookie domain defaults to `.melispy.com` and login sets that wide domain.
  Config and sink: `app/config.py:38` and `app/routes/auth.py:151`.

## Endpoints

- `POST /v1/auth/signup`
- `POST /v1/auth/verify`
- `POST /v1/auth/login`
- `POST /v1/auth/forgot`
- `POST /v1/auth/reset`
- `POST /v1/auth/refresh`
- `POST /v1/auth/logout`
- `GET /v1/auth/sessions`
- `DELETE /v1/auth/sessions/{session_id}`
- `POST /v1/legacy/auth/verify`
- `GET /v1/health/live`
- `GET /v1/health/ready`
