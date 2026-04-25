# CLAUDE.md — Melispy Inc. v3.0 (repo-specific)

Overrides global `~/.claude/CLAUDE.md` where noted. User message always wins.

## Effort

Always `xhigh` for any v3 work. Never drop to medium/low without explicit operator instruction.
Max effort + ultrathink on architecture, security, vuln design, and deployment decisions.

## Branch

Active worktree: `worktree-v3-melispy-baseline`. Push per-phase to this branch.
Merge to `main` only after v3.0.0 ships + first engagement (Phase 7) passes.

## Stack (per MASTER-PROMPT-V3.md Section 2 decisions)

- Frontend: Next.js 16 RSC + server actions, Tailwind v4 CSS-first, shadcn-style custom components, TanStack Query v5, Zod v4
- Backend: Python 3.11+ FastAPI, Pydantic v2, SQLAlchemy 2.0, alembic, uv
- Data: Postgres 16 (multi-schema), Redis 7, MinIO
- Secrets: HashiCorp Vault dev mode
- Mesh: Traefik mTLS, OPA Rego
- Infra: Docker Compose v2
- LLM: deterministic fixtures ONLY — no real API calls

## Hard Bans

- No copying code from Juice Shop, DVWA, WebGoat, Mutillidae, vulhub, exploit-db PoCs
- No real LLM API calls (costs prohibitive + non-reproducible)
- No Sonnet 4.6 or Haiku subagents — Opus 4.7 max effort only
- No `/docs`, `/redoc`, `/openapi.json` accessible in production configs
- No hardcoded credentials in committed files (even fake ones)
- No `--no-verify`, `--no-gpg-sign` on commits
- No `rm -rf` on shared paths without explicit operator confirm

## Tooling Preferences

- `/codex` for substantial multi-file implementations (>200 LOC)
- Subagent forks (no subagent_type) for context-heavy parallel tasks
- `/code-review` after each phase commit
- `/simplify` after review finds over-engineering
- Context7 MCP for version-sensitive lib docs

## Vuln Annotation Convention

Intentional vulns must be annotated in code:
```python
# VULN: V-T<tier>-<seq> — <one-line description>
```
`make catalog-validate` checks annotations match VULN-CATALOG.md.
