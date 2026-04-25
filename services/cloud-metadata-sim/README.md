# Cloud Metadata Simulator

FastAPI simulator for the AWS EC2 IMDSv1 metadata service used by the Melispy v3
sparring lab.

This service intentionally exposes unauthenticated metadata and STS-style
credentials to model V-T8-001:

SSRF chain -> cloud metadata -> STS-style token -> cross-service auth.

The service is designed to be reachable through the compose alias
`169.254.169.254 -> metadata-sim` when Phase 4 adds the infrastructure entry.

## Development

```bash
uv pip install -e ".[dev]"
pytest -q
ruff check app tests
```

## Runtime

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```
