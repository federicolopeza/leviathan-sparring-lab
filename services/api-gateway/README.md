# Melispy API Gateway

Single ingress for `api.melispy.com`.

## Routes

- `/v1/auth/*` -> `AUTH_SERVICE_URL`
- `/v1/legacy/auth/*` -> `AUTH_SERVICE_URL`
- `/v1/users/*` -> `USERS_SERVICE_URL`
- `/v1/orgs/*` -> `ORGS_SERVICE_URL`
- `/v1/health/live` and `/v1/health/ready` are served by the gateway.

Protected upstreams require `Authorization: Bearer <jwt>`. The gateway verifies RS256 JWTs,
applies tiered rate limits, forwards identity headers, and emits audit records.

## Local checks

```bash
uv run ruff check app/ tests/
uv run pytest tests/ -x -q
```
