# Melispy Orgs Service

FastAPI service for organization, membership, and invitation management in Melispy v3.

## Endpoints

- `POST /v1/orgs`
- `GET /v1/orgs/me`
- `GET /v1/orgs/{org_id}`
- `PATCH /v1/orgs/{org_id}`
- `GET /v1/orgs/{org_id}/members`
- `POST /v1/orgs/{org_id}/members`
- `DELETE /v1/orgs/{org_id}/members/{user_id}`
- `POST /v1/orgs/{org_id}/invitations`
- `POST /v1/orgs/invitations/accept`
- `GET /v1/orgs/{org_id}/invitations`
- `GET /v1/health/live`
- `GET /v1/health/ready`

## Intentional vulnerabilities

- `V-T1-003`: `/v1/health/ready` exposes build metadata.

## Phase 2 placeholders

- `V-T3-001`: tenant scope checks on org/member reads are intentionally safe in Phase 1.
- `V-T3-006`: invitation tokens are cryptographically random in Phase 1.

## Local validation

```bash
PYTHONPATH=../_shared python -m pytest tests/ -v
ruff check app/ tests/
```
