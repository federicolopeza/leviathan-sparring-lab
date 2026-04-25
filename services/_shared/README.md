# melispy_shared

Shared Python library for Melispy v3 microservices. It provides JWT helpers,
async SQLAlchemy setup, audit-chain primitives, OPA policy evaluation,
Redis-backed rate limiting, and request-id logging middleware.

This package is intentionally dual-use inside the sparring lab: it includes safe
service primitives and a small set of explicitly annotated vulnerabilities that
map to the v3 benchmark catalog.

## Threat Model

The shared library sits on the trust boundary between the API gateway,
microservices, Postgres, Redis, and OPA. Attackers may control HTTP headers,
JWT headers, JWT algorithms, uploaded key material, and authenticated service
inputs. Production hardening should remove or gate every intentional vuln below.

### Intentional Vulnerabilities

- `V-T2-004` — `melispy_shared/auth.py:legacy_verify`
  - Chain hint: forge a mobile legacy JWT after bypassing per-IP lockout.
  - CVSS estimate: 8.1 High.

- `V-T2-006` — `melispy_shared/rate_limit.py:_client_ip`
  - Chain hint: rotate spoofed `X-Forwarded-For` values to bypass lockout.
  - CVSS estimate: 6.5 Medium.

- `V-T5-002` — `melispy_shared/auth.py:verify_jwt_unsafe_alg_confusion`
  - Chain hint: switch RS256 to HS256 and sign with the RSA public key as HMAC secret.
  - CVSS estimate: 9.1 Critical.

- `V-T5-003` — `melispy_shared/auth.py:verify_jwt_kid_path`
  - Chain hint: use `kid` traversal to select attacker-controlled signing key material.
  - CVSS estimate: 8.8 High.
