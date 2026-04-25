# HANDOFF — Leviathan Sparring Lab v3 (Melispy Inc.)

**Last updated:** 2026-04-25
**Branch:** worktree-v3-melispy-baseline
**Active session goal:** Phase 2 — Business services + T3-T4 vulns

---

## Current phase: Phase 2 (in_progress)

### Commits
- `fa65c5e` Phase 0 — foundation (frontend skeleton, auth-service, data tier)
- `668f95a` Phase 1 — core microservices + T1-T2 vulns
- Phase 2 in progress (not yet committed)

### Phase 2 T3/T4 vulns baked (ready to commit)

| ID | File | Status |
|---|---|---|
| V-T3-001 BOLA | `orgs-service/app/routes/orgs.py:69`, `members.py:43` | ✅ baked |
| V-T3-002 IDOR | `users-service/app/routes/users.py:88` | ✅ baked |
| V-T3-003 mass-assign | `users-service/app/schemas/users.py:13`, `routes/users.py:66` | ✅ baked |
| V-T3-006 weak token | `orgs-service/app/routes/invitations.py:109` | ✅ baked |
| V-T4-003 SSRF avatar | `users-service/app/routes/users.py:124` | ✅ baked |
| V-T4-007 stored XSS | `users-service/app/routes/users.py:70` | ✅ baked |

### Phase 2 service scaffolds (Codex agents building in parallel)

| Service | Status | Vulns to bake |
|---|---|---|
| billing-service | Codex agent running (a8c5fc8d) | V-T4-001 race, V-T4-002 coupon, V-T4-011 negative qty |
| uploads-service | Codex agent running (a69b379d) | V-T4-005 traversal, V-T4-006 polyglot |
| search-service | Codex agent running (a5d3d31c) | V-T4-008 SQLi |
| webhooks-service | Codex agent running (a2cf34cc) | V-T4-004 SSRF, V-T4-010 replay |
| frontend (billing/uploads/webhooks pages) | Codex agent running (af6bd0a1) | — |

### Infrastructure updates (ready to commit)

- `infra/docker-compose.yml` — 8 new microservice blocks (api-gateway through webhooks-service)
- `services/api-gateway/app/config.py` — 4 new service URL fields
- `services/api-gateway/app/upstreams.py` — 4 new upstreams (billing/uploads/search/webhooks)
- `frontend/lib/schemas.ts` — Zod schemas for billing/uploads/webhooks (added by T3-T4 baker)
- `VULN-CATALOG.md` — T3/T4 rows updated to baked-v3.0.0 with file:line refs

---

## What to do when Codex agents complete

When the 5 Codex agents notify completion, integrate their work:

1. Check each new service has: `main.py`, routes, schemas, alembic migration, Dockerfile, pyproject.toml, tests
2. Verify V-T4-001/002/004/005/006/008/010/011 annotations are in place
3. Commit Phase 2 as one atomic commit: `feat(v3-phase2): business services + T3-T4 vulns`
4. Then dispatch Phase 3 agents: agents-service, llm-service, chat widget, T5-T6 vulns

---

## Phase roadmap

- [x] Phase 0 — Foundation
- [x] Phase 1 — Core microservices + T1-T2 vulns
- [ ] **Phase 2** — Business services + T3-T4 vulns (IN PROGRESS)
- [ ] Phase 3 — AI integration + T5-T6 vulns
- [ ] Phase 4 — Lateral + Elite + T7-T8 vulns
- [ ] Phase 5 — Defense escalation + observability v3
- [ ] Phase 6 — Loop tooling + legacy cleanup + release v3.0.0
- [ ] Phase 7 — First adversarial run + iteration

---

## Quality gates before Phase 2 commit

```bash
cd services/users-service && python -m pytest -x -q
cd services/orgs-service && python -m pytest -x -q
cd services/api-gateway && python -m pytest -x -q
cd services/billing-service && python -m pytest -x -q 2>/dev/null || echo "tests pending"
cd services/uploads-service && python -m pytest -x -q 2>/dev/null || echo "tests pending"
cd services/search-service && python -m pytest -x -q 2>/dev/null || echo "tests pending"
cd services/webhooks-service && python -m pytest -x -q 2>/dev/null || echo "tests pending"
```

## Useful commands

```bash
git log --oneline -10
git diff HEAD --stat
git status --short
```
