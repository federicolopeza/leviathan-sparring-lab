# HANDOFF — Leviathan Sparring Lab v3 (Melispy Inc.)

**Last updated:** 2026-04-25
**Branch:** worktree-v3-melispy-baseline
**Active session goal:** Phase 5 — Defense escalation + observability v3

---

## Current phase: Phase 5 (NEXT — Phase 4 complete)

### Commits (latest first)

- `feat(v3-phase4)` — lateral + elite chains + T7-T8 vulns (JUST COMMITTED)
- `2f33b01` fix(search-service): correct V-T4-008 SQLi reproducer payload
- `a097b45` feat(v3-phase3): llm-service + V-T5-002/003 JWT vulns + V-T6-002/003
- `a79a489` feat(v3-phase3): agents-service + V-T5-001 IDOR + V-T6-001 SSTI
- `278af2c` feat(v3-phase2): business services + T3-T4 vulns baked
- `668f95a` feat(v3-phase1): core microservices + T1-T2 vulns
- `fa65c5e` feat(v3-phase0): foundation

---

## Phase 4 — COMPLETE (52 vulns baked)

### What was built

| Service | Key vulns | Tests |
|---|---|---|
| admin-service | V-T3-004 (X-Cluster-Internal bypass), V-T4-007 (XSS in bio), V-T4-009 (SSTI Jinja2), V-T7-002 (Vault token in env) | 8 passed |
| notifications-service | V-T7-005 (MinIO root creds), V-T6-006 (ImageMagick SVG), V-T6-007 (wkhtmltopdf cmd injection) | 7 passed |
| cloud-metadata-sim | V-T8-001 (IMDSv1 unauthenticated, fake STS creds) | 7 passed |
| infra/docker-compose.yml | V-T7-006 (docker.sock in promtail), admin+notifications+cloud-metadata-sim added | — |
| engagements/_baseline-exploits/ | V-T8-001, V-T8-005, V-T8-006 chain scripts | — |
| infra/ca/ROADMAP.md | V-T7-001 single-CA design documentation | — |
| VULN-CATALOG.md | All 52 vulns updated (T4-T8 deferred → baked-v3.0.0) | — |

---

## Phase 5 plan (NEXT)

Dispatch 6 parallel agents:

```
Agent 1 — opa-policies (Codex)         # infra/opa/policies/*.rego
Agent 2 — postgres-rls (Codex)         # infra/postgres/init/rls.sql + app deps
Agent 3 — mtls-mesh (fork)             # infra/ca/ real certs + traefik tls dynamic config
Agent 4 — audit-signing (Codex)        # melispy_shared/audit.py verify_chain used in admin-service
Agent 5 — grafana-dashboards (fork)    # infra/grafana/dashboards/*.json (4 dashboards)
Agent 6 — loki-alerts (Codex)          # infra/loki/ruler/*.yaml + Discord webhook
```

Acceptance:
- OPA evaluates every api-gateway request; logs allow/deny
- RLS on Postgres prevents cross-tenant query even with shared creds
- mTLS verified between every internal service pair (Traefik TLS client-auth)
- Audit log entries verifiable via HMAC chain
- Grafana dashboards: rate-limits, auth-failures, search-queries, SSRF-attempts
- Loki alert fires on SQL injection pattern → Discord webhook test

Commit: `feat(v3-phase5): defense escalation + observability v3`

---

## Phase roadmap

- [x] Phase 0 — Foundation
- [x] Phase 1 — Core microservices + T1-T2 vulns
- [x] Phase 2 — Business services + T3-T4 vulns
- [x] Phase 3 — AI integration + T5-T6 vulns
- [x] **Phase 4** — Lateral + Elite + T7-T8 vulns (COMPLETE)
- [ ] **Phase 5** — Defense escalation + observability v3 (NEXT)
- [ ] Phase 6 — Loop tooling + legacy cleanup + release v3.0.0
- [ ] Phase 7 — First adversarial run + iteration

---

## Useful commands

```bash
git log --oneline -10
git diff HEAD --stat
git status --short
cd services/admin-service && python -m pytest -x -q
cd services/notifications-service && python -m pytest -x -q
cd services/cloud-metadata-sim && python -m pytest -x -q
```
