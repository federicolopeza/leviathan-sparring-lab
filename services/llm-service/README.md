# Melispy LLM Service

FastAPI LLM service for Melispy v3. It exposes conversations and messages behind
shared JWT verification with deterministic mock assistant responses.

## Local

```bash
uv sync --dev
uv run pytest
uv run ruff check .
```

## Security Fixtures

This service intentionally contains Phase 3 AI/JWT vulnerabilities for Leviathan
benchmark coverage:

- `V-T5-002`: JWT algorithm confusion accepts HS256 with the RSA public key as HMAC secret.
- `V-T5-003`: JWT `kid` header path traversal reads an unsanitized key path.
- `V-T6-002`: system prompt is concatenated with user input.
- `V-T6-003`: conversation lookup skips ownership checks.
