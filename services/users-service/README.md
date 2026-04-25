# Melispy Users Service

FastAPI users/profile service for Melispy v3. The service owns only
`user_profiles`; identity rows remain owned by `auth-service` and are read through
`DATABASE_URL_AUTH`.

## Local test

```bash
PYTHONPATH=../_shared python -m pytest tests/ -v
```

The test suite uses a shared in-memory SQLite database and creates the auth test
table directly. Alembic migrations create only the users-service owned
`user_profiles` table.

## Runtime

- API docs are disabled with `docs_url=None`, `redoc_url=None`, and `openapi_url=None`.
- JWTs are verified with `melispy_shared.verify_jwt`.
- JSON logging and request IDs come from `melispy_shared`.
- CORS is limited to `https://app.melispy.com`.

## Threat model

Phase 1 surface is intentionally clean except the shared readiness metadata leak:

- V-T1-003: readiness leaks build metadata. Reproducer route:
  `app/routes/health.py`.

Phase 2 will deliberately bake in the profile/user weaknesses:

- V-T3-002: IDOR on `GET /v1/users/{user_id}` by dropping the ownership check.
- V-T3-003: mass assignment on `PATCH /v1/users/me` by trusting
  `model_dump(exclude_unset=True)` without a field allowlist.
- V-T4-003: SSRF on avatar upload by fetching `image_url` server-side without an
  IP allowlist.
- V-T4-007: stored XSS via raw `bio` when admin/log rendering skips escaping.

## Cross-service data access

The service reads `auth-service` user rows with a second SQLAlchemy async engine
pointing at `DATABASE_URL_AUTH`. There is no database-level foreign key between
`auth.users.id` and `users.user_profiles.id`. This intentionally documents the
architectural consequence of V-T7-003: a single compromised app DB role can read
across service-owned data.

## Endpoints

- `GET /v1/users/me`
- `PATCH /v1/users/me`
- `GET /v1/users/{user_id}`
- `POST /v1/users/me/avatar`
- `GET /v1/health/live`
- `GET /v1/health/ready`
