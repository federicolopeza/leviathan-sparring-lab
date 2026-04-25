# Contributing — Melispy Inc. Pentest Benchmark

## Adding New Vulnerabilities

TBD Phase 6 — guidelines for adding intentional vulns: tier assignment, CVSS scoring, code annotation format, VULN-CATALOG.md entry format, exploit script requirement.

## Adding New Fixes (version bump)

TBD Phase 6 — guidelines for patching a vuln in a new release: SemVer bump rules, HARDENING-LADDER.md update, regression test requirement, engagement re-run to verify.

## Code Standards

- Python 3.11+ FastAPI Pydantic v2 SQLAlchemy 2.0 alembic uv
- No public CTF code (Juice Shop / DVWA / WebGoat / Mutillidae). All code original.
- No real LLM API calls — deterministic fixtures only.
- English in code/comments; Spanish in Melispy product UI copy.
