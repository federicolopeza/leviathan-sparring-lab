# HANDOFF — Leviathan Sparring Lab v3 (Melispy Inc.)

**Last updated:** 2026-04-25
**Branch:** worktree-v3-melispy-baseline
**Tag:** v3.0.0 → `5f053a4` (pushed + force-updated)
**GitHub Release:** https://github.com/federicolopeza/leviathan-sparring-lab/releases/tag/v3.0.0
**Active session goal:** Phase 7 — First adversarial run + iteration

---

## RELEASE: v3.0.0 — COMPLETE

### Commit history (Phase 0-6)

```
7e89572 docs(v3): public README v3.0
06aaf48 chore(cleanup): remove legacy v1/v2 assets + loop tooling
1433f98 feat(v3-phase5): defense escalation + observability v3
154cec2 feat(v3-phase4): lateral + elite chains + T7-T8 vulns
2f33b01 fix(search-service): correct V-T4-008 SQLi reproducer payload
a097b45 feat(v3-phase3): llm-service + V-T5-002/003 JWT vulns
a79a489 feat(v3-phase3): agents-service + V-T5-001 IDOR + V-T6-001 SSTI
880a625 feat(v3-phase3): frontend agents + chat pages
fcaf346 feat(v3-phase3): wire agents+llm into gateway + update catalog T5-T6
278af2c feat(v3-phase2): business services + T3-T4 vulns baked
668f95a feat(v3-phase1): core microservices + T1-T2 vulns
fa65c5e feat(v3-phase0): foundation
```

---

## What was built (all phases)

| Phase | Deliverable | Tests |
|---|---|---|
| 0 | Foundation: auth-service, frontend skeleton, data tier | all pass |
| 1 | Core: api-gateway, users, orgs, search, shared lib | all pass |
| 2 | Business: billing, webhooks, uploads, honeypot | all pass |
| 3 | AI: agents-service, llm-service, frontend chat | all pass |
| 4 | Lateral: admin-service, notifications-service, cloud-metadata-sim, T7-T8 | 22 pass |
| 5 | Defense: OPA, Postgres RLS, mTLS certs, Grafana 4 dashboards, Loki alerts, Falco | 8 pass (shared) |
| 6 | Loop tooling: Makefile v3, triage.py, legacy cleanup, README, v3.0.0 tag | — |

### Vulnerability count: 52 baked
T1:5 T2:6 T3:7 T4:11 T5:5 T6:7 T7:5 T8:6

---

## Phase 7 — First adversarial run (NEXT)

```bash
# 1. Start engagement
make engage ENG=LEV-MELISPY-V3-001

# 2. Run Leviathan against melispy.com v3.0.0 (24h window)
#    Output: engagements/LEV-MELISPY-V3-001/findings.json

# 3. Triage
make triage ENG=LEV-MELISPY-V3-001

# 4. Score
make score ENG=LEV-MELISPY-V3-001

# 5. Patch unexpected wins → bump v3.0.1
```

### Known deferred vulns (baked-deferred → Phase 5 or 7)
- V-T7-001 (mTLS shared cert) — infra/ca/ROADMAP.md documents, cert gen script created, not yet deployed
- V-T5-006 (same CA) — inherits from above

---

## Useful commands

```bash
git log --oneline -10
git tag -l v3*
make test
make smoke
make engage ENG=LEV-MELISPY-V3-001
make triage ENG=LEV-MELISPY-V3-001
```
