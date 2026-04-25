# Melispy Billing Service

FastAPI billing service for Melispy v3. It exposes plans, carts, coupons, checkout,
mock payments, and invoices behind shared JWT verification.

## Local

```bash
uv sync --dev
uv run pytest
uv run ruff check .
```

## Security Fixtures

This service intentionally contains Phase 2 business-logic vulnerabilities for
Leviathan benchmark coverage:

- `V-T4-001`: checkout idempotency/race double charge.
- `V-T4-002`: repeated coupon stacking on the same cart.
- `V-T4-011`: negative quantity accepted into billing totals.
- `V-T1-003`: readiness endpoint leaks build metadata.
