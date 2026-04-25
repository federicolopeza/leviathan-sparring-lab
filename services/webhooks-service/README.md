# Melispy Webhooks Service

FastAPI service for user-managed outbound webhooks in Melispy v3.

## Endpoints

- `POST /v1/webhooks`
- `GET /v1/webhooks`
- `PATCH /v1/webhooks/{webhook_id}`
- `DELETE /v1/webhooks/{webhook_id}`
- `POST /v1/webhooks/{webhook_id}/test`
- `GET /v1/webhooks/{webhook_id}/deliveries`
- `POST /v1/webhooks/_internal/dispatch`
- `GET /v1/health/live`
- `GET /v1/health/ready`

## Intentional vulnerabilities

- `V-T1-003`: `/v1/health/ready` exposes build metadata.
- `V-T4-004`: webhook URL blocklist only rejects `192.168.0.0/16`.
- `V-T4-010`: webhook retry attempts regenerate `event_id`.

## Local validation

```bash
PYTHONPATH=../_shared python -m pytest tests/ -v
ruff check app/ tests/
```
