# Leviathan Sparring Lab — Vultr 24h ephemeral deploy plan (índice)

**Version:** 2026-04-23 · **Supersedes:** `leviathan-claude-code/server.md` (Hetzner Plan 1)
**Target:** empirical benchmark of Leviathan 8.2 against 28-stack zoo, Vultr VPS, destroy-after 24h, <$5 infra.

Plan documental dividido en 13 archivos bajo `docs/` por concerns. Este archivo es solo índice.

---

## Resumen ejecutivo

- **Provider:** Vultr `vhp-8c-16gb-amd` ($0.143/h × 24h = $3.43)
- **28 stacks vulnerables** (CMS/API/identity/CI-CD/cloud-sim/k8s/mail/IoT/AI/mobile/VoIP/SCADA)
- **131 ground truth entries** para medir recall/precision
- **Hardened afuera** (Cloudflare WAF + firewall + tunnel) + **vulnerable adentro**
- **Leviathan 8.2** ataca 24h: STEALTH → TACTICAL → WARFARE → chaos → analysis → teardown
- **Kill-switch real wired** (file + HTTP 503 + middleware gate)
- **Hash-chain evidence** — teardown aborta si chain rota
- **Destroy-after genuino** — Vultr + Cloudflare + WireGuard cleanup verified

Cost realístico por corrida: **$18-29 USD** (infra + tokens Opus).

---

## 10 mejoras obligatorias vs Plan 1 (Hetzner)

1. **Full Vultr migration** — `vultr/vultr ~>2.21` provider, `vultr_instance` + `vultr_firewall_group` + `vultr_firewall_rule`
2. **Tripwire removido** (redundante con AIDE, cuts 3 min bootstrap)
3. **Kill-switch real implementation** (Traefik static route + file marker + operator script + hour-0 validation)
4. **Postmortem §11 token economics** (USD/finding × tier, findings/USD, cache hit rate)
5. **Ground truth 3 stubs → 131 entries** (≥ 3/stack, CVE-pinned + intentional labs + OWASP LLM)
6. **Runbook hour 8-16 expandido** (/deep-hunter, /web-hunter, /source-audit --auto-clone, /waf-bypass)
7. **Observability smoke gate** — 8 checks bloquean benchmark si obs no ingesta
8. **Evidence export hash-chain gated** — chain rota → teardown aborta, state dumped
9. **Vultr edge cases** (cloud-init firewall, vnstat cap, snapshots off, metadata block)
10. **CI/CD seeded Git repos** con fixture tokens → enable `/supply-chain` → `/cloud-audit` chain

---

## Índice — carpeta `docs/`

### [00 — Overview](docs/00-overview.md)

Explicación fácil. Analogía. Flujo 24h. Por qué partimos en carpetas. Quién lee qué.

### INFRA (lo que Claude construye antes del benchmark)

- **[01 — Architecture](docs/01-architecture.md)** — Topología red, 12 Docker bridges, Cloudflare config, Vultr edge cases, WireGuard
- **[02 — Infrastructure](docs/02-infrastructure.md)** — Repo layout, `.env.lab`, **Terraform Vultr completo**, preflight, Ansible 9-role, Makefile, timing
- **[03 — Hardening](docs/03-hardening.md)** — Paquetes, sysctl, auditd, AppArmor, Docker (userns-remap + seccomp), Fail2ban + CrowdSec, Falco, **kill-switch real**
- **[04 — Zoo Targets](docs/04-zoo-targets.md)** — 28 stacks por grupo (A-I), pinning, **CI/CD seeded repos** con fixture tokens
- **[05 — Ground Truth](docs/05-ground-truth.md)** — Schema, distribución 131 entries, ejemplos (wordpress/jenkins/dvga/minio cross-stack), validación
- **[06 — Observability](docs/06-observability.md)** — Wazuh/Suricata/Falco/Tetragon/Arkime/Loki/Grafana/ModSec/honeytokens, **8 dashboards**, **smoke gate 8-check**

### LEVIATHAN (lo que ejecuta durante 24h)

- **[07 — ROE](docs/07-roe.md)** — `lab.yaml` completo, scope, deny_actions, safety_limits, Mythos tiers, hash-chain, kill-switches, auto-chain 0-4, dynamic model resolution, hot-swap
- **[08 — Runbook](docs/08-runbook.md)** — 7 ventanas hora-por-hora (deploy → STEALTH → TACTICAL → WARFARE → chaos → analysis → teardown), decision tree, comandos mid-run
- **[09 — Metrics + Scoring](docs/09-metrics-scoring.md)** — Offensive + defensive metrics, scoreboard CSV 20-col, scoring rules (Coverage/Exploit/Precision/WAF Friction/Tier Gain/Hash Integrity/Chain Bonus), targets, per-skill FP rate, cost accounting
- **[10 — Postmortem](docs/10-postmortem.md)** — Template 11 secciones, §11 token economics per-tier breakdown, verdict WARFARE justified?

### OPS (scripts + checklists)

- **[11 — Operations](docs/11-operations.md)** — 9 scripts (bootstrap/teardown/smoke/kill/preflight/export/scoreboard/wg-keys/reconcile), Makefile, flujo one-shot, comandos mid-run, rotation policy, recovery
- **[12 — Checklists](docs/12-checklists.md)** — Pre-deploy (16 items) + post-teardown (16 items), success criteria, **cost projection detallado**, region selection, plan fallback, hard limits, go/no-go

---

## Scaffold pendiente

Docs completos. Falta materializar ~60 archivos reales:

- `terraform/` (5 files)
- `ansible/` (9 roles, ~25 files)
- `targets/` (35 Dockerfiles + 3 seed-repos)
- `docker-compose.yml` (1 file, 28 services + obs)
- `ground_truth/ground_truth.yml` (131 entries)
- `scripts/` (9 executables)
- `lab.yaml` (ROE file)
- Root: `README.md`, `Makefile`, `.env.lab.example`, `.gitignore`, `postmortem-template.md`

Se ejecuta con 3 subagents en paralelo (worktrees):
- `terraform-migrator`
- `ground-truth-populator`
- `target-dockerfile-builder`

Operador decide cuándo arrancar scaffold.

---

## Next steps

1. Review docs (cualquier docs/ que requiera ajuste)
2. **Operador decide:** scaffold ahora o después
3. Scaffold (3 subagents paralelos, ~30 min)
4. Operador crea VPS Vultr + dominio + llena `.env.lab`
5. `./scripts/bootstrap.sh`
6. Benchmark 24h per [runbook](docs/08-runbook.md)
7. `./scripts/teardown.sh`
8. Postmortem llenado
