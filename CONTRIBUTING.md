# Contributing — Melispy Inc. Pentest Benchmark

## Adding New Vulnerabilities

1. **Tier assignment**: pick the lowest tier whose definition the vuln satisfies (T1 passive → T8 elite chain).
2. **CVSS**: use CVSS 3.1 AV:N/AC:L base estimate. Minimum 4.0 to qualify.
3. **Code annotation**: add `# V-Txx-xxx INTENTIONAL VULN: <one-line description>` at the exact vulnerable line.
4. **VULN-CATALOG.md entry**: add row with `ID | Title | Service | File:Line | CVSS | Chain | baked-v3.x.x`.
5. **Exploit script**: add `engagements/_baseline-exploits/V-Txx-xxx-<slug>.py` demonstrating the exploit end-to-end.
6. **Test**: add `test_v_txx_xxx_<slug>` to the service's test suite; the test must PASS (reproducing the vuln).
7. **PR**: title `feat(vulns): V-Txx-xxx <title>`. Reference the tier in the description.

## Adding New Fixes (version bump)

1. Remove or neutralize the intentional annotation.
2. Add a hardening test that verifies the fix (must FAIL against the unfixed version).
3. Update VULN-CATALOG.md status → `patched-pending-verify`.
4. Update `HARDENING-LADDER.md` with the fix entry.
5. Bump SemVer patch: `v3.0.0 → v3.0.1`.
6. Run `make triage ENG=<id>` after re-engagement to verify the vuln is no longer findable.

## Engagement workflow

```bash
make engage ENG=<your-id>              # creates engagements/<id>/ROE.md
# run your framework against localhost:8080
# write findings to engagements/<id>/findings.json
make triage ENG=<your-id>             # produces scored triage-report.md
make score ENG=<your-id>              # just prints score summary
```

Findings format:
```json
{"findings": [{"vuln_id": "V-T2-001", "evidence": "curl output...", "notes": "600ms delta"}]}
```

## Code standards

- Python 3.12+ FastAPI Pydantic v2 SQLAlchemy 2.0 alembic uv
- `ruff check` + `mypy --strict` must pass per service
- TypeScript: `tsc --noEmit` + `eslint` must pass
- No public CTF code (Juice Shop / DVWA / WebGoat / Mutillidae). All code original.
- No real LLM API calls — deterministic fixtures only.

## License

MIT. By contributing you agree that your contribution is licensed under MIT.
