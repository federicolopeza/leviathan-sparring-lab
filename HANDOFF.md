# HANDOFF — Leviathan Sparring Lab

**Last updated:** 2026-04-25
**Active operator:** Federico
**Active session goal:** Bootstrap v2 lab (lean + hardened) + reorg repo

---

## Where we are

- **Plan v2 escrito** ([vultr-deploy-plan.md](vultr-deploy-plan.md)) — supersedes v1 (28-stack benchmark)
- **Repo en transición** v1 → v2:
  - v1 scaffold sigue en disco (37 targets, 28-stack compose, etc) — NO romper
  - v2 introduce: `docker-compose.lean.yml`, `scripts/lab-up.sh`/`lab-down.sh`/`gt-rotate.sh`, `docs/14-defense-playbook.md`, etc
  - v1 `docker-compose.yml` se renombrará a `docker-compose.legacy.yml` cuando v2 esté testeado

## VPS state

| Item | Status |
|---|---|
| VPS Santiago `levlab-ephemeral` (f2e6ab03-5c98-4dea-b2bc-0ae34969a465) | ✅ **LIVE** desde 2026-04-25 |
| VPS Santiago IP | `64.176.15.72` |
| Plan | `vhp-2c-4gb-amd` $24/mo |
| OS | Debian 12 bookworm fresh |
| Hardening phases | 7/9 (base/sysctl/fail2ban/auditd/docker/cloudflared/wireguard) — **ssh+ufw deferred** (lockout risk) |
| Docker | 28.5.2 (downgrade desde 29.x por Traefik client lib) |
| Stack | 11 containers UP (cloudflared/traefik/kali/metasploit/loki/promtail + 6 GTs 2026) |
| External | ✅ 6 GTs reachables via tunnel |
| VPS viejo NJ `levlab-ephemeral` (e754ad58-...) | Running, **destroy pendiente** |
| VPS viejo IP | `140.82.60.135` |
| Snapshot 480GB (97fcac9e-...) | Available, **delete pendiente** (cuesta $24/mo storage) |

## Cloudflare state

- Domain: `melispy.com` ✅ activa
- Tunnel `levlab-tunnel` (`fb194e68-...`) ✅ 4 conexiones activas (scl06 + gru07)
- Tunnel ingress: 15 hostnames + catchall 404 ✅ apunta a Traefik via mgmt_net
- DNS records explícitos (NO wildcard): apex + 17 subdomains, todos proxied
  - Surface 2026: agent/ai, chat/assistant, billing/saas, mobile/app, shop/store, www, lab, gt, traefik
- WAF: Free plan default rules. Custom rules anti-scanner UA: **pendiente** (Fase 4)
- WAF Rate Limiting Rules: **pendiente**
- CF Access (zero-trust admin): **pendiente** (para `traefik.melispy.com` / `grafana.melispy.com`)

## Cuenta Vultr

- API key pegada en chat = QUEMADA. **Rotar urgente** post-bootstrap (Account → API → Regenerate)
- ACL allowlist `179.24.190.234/32` activa ✅
- Tras rotar: actualizar `.env.lab` + scripts que referencien `VULTR_API_KEY`

## Engagement Gonxa

- ID: `LEV-MELISPY-GONXA-001` (v1, target era 28-stack lab)
- v2 abrirá `LEV-MELISPY-GONXA-002` con target hardened
- `GONXA-BRIEFING.md` necesita update con changes v2 antes de mandárselo
- Window 24h aún no agendada

## Decisiones pendientes (operador)

Ver `vultr-deploy-plan.md` sección "Decisiones pendientes". Tomar antes de Fase 2:

1. Burp en VPS o solo laptop
2. Primer GT activo (DVWA / Juice Shop / crapi / etc)
3. Falco día 0 o opt-in
4. Honeypot cowrie sí/no
5. Snapshot 480GB rescatar o delete directo
6. VPS NJ destroy ya o esperar
7. Lifecycle: ephemeral o 24/7
8. Cloudflare Free vs Pro

## Próximo paso operador

1. Crear Firewall Group Vultr `levlab-strict` (SSH 22 + ICMP desde `179.24.190.234/32`)
2. Deploy fresh VPS Santiago Debian 12 `vhp-2c-4gb-amd` con SSH key `autop2p-migration`
3. Pasar IP nuevo

## Próximo paso Claude

Cuando llegue IP:

1. Update `.env.lab` con `VULTR_VPS_IP=<nuevo>`
2. Crear archivos Fase 2 (compose lean, scripts lifecycle, harden script)
3. Update `README.md` quickstart para v2
4. Crear `docs/14-defense-playbook.md`
5. Renombrar `docker-compose.yml` → `docker-compose.legacy.yml`

## Files tocados sesión actual

**Created v2:**
- `vultr-deploy-plan.md` — rewrite v2 (lean + hardened, anti-Gonxa)
- `HANDOFF.md` — this file
- `README.md` — quickstart v2
- `docker-compose.lean.yml` — 6 core + opt-in profiles (defense/honeypot/dashboards)
- `Makefile` — slim v2 targets
- `targets/catalog.yml` — 36 stacks metadata (CVE, severity, gonxa_pain)
- `docs/14-defense-playbook.md` — anti-recon + anti-attack + IR
- `scripts/lab-up.sh` — bootstrap deploy (rsync + harden + compose up)
- `scripts/lab-down.sh` — snapshot + destroy lifecycle (Vultr API)
- `scripts/gt-rotate.sh` — swap GT activo via catalog.yml
- `scripts/harden.sh` — idempotent OS hardening 9 phases
- `legacy/README.md` — explica contenido legacy
- `deploy/seccomp/levlab-default.json` — copied from legacy

**Moved to `legacy/`:**
- `docker-compose.yml` (28 stacks v1)
- `deploy/docker-compose.prod.yml` (22 stacks variant)
- `ansible/` (entire — 9 roles v1)
- `scripts/bootstrap.sh` (Terraform-based v1)
- `scripts/teardown.sh` (24h destroy-after v1)
- `Makefile` (v1)

**Deleted:**
- `scripts/__pycache__/`

## Files pendientes crear/editar

**High priority (post-IP):**
- `.env.lab` — actualizar con `VULTR_VPS_IP=<nuevo>` + `OPERATOR_IP=179.24.190.234` + `SSH_PORT=49222` + `SSH_USER_HARDENED=levop`
- `.env.lab.example` — agregar nuevas vars (GT_IMAGE, GT_PORT, GT_ACTIVE, OPERATOR_IP, SSH_USER_HARDENED, GRAFANA_ADMIN_PW)
- `deploy/falco/falco_rules.local.yaml` — custom rules anti-Gonxa TTPs (referenced in compose)
- `deploy/observability/grafana/provisioning/` — datasources + dashboards provisioning
- `scripts/smoke.sh` — refactor para 6 containers (currently v1 oriented)
- `scripts/waf-test.sh` — verify CF rules
- `scripts/lynis-baseline.sh` — score gate
- `scripts/trivy-scan.sh` — image scan

**Medium priority:**
- Re-scope `docs/00-overview.md` con analogía v2
- Re-scope `docs/01-architecture.md` (3 nets vs 12)
- Re-scope `docs/03-hardening.md` (mover checklist épico)
- Re-scope `docs/06-observability.md` (recortar a Loki+Promtail)
- Rename + re-scope `docs/04-zoo-targets.md` → `04-targets-catalog.md`
- Re-scope `docs/11-operations.md` (scripts nuevos)
- Re-scope `docs/12-checklists.md` (v2 pre/post)
- `terraform/main.tf` — agregar WAF custom rules anti-bot

**Low priority (post-deploy):**
- Re-scope resto `docs/`
- `GONXA-BRIEFING.md` update con changes v2
- `engagements/LEV-MELISPY-GONXA-002/` (cuando se agende)

## Comandos útiles para retomar

```bash
# Resumen estado
git log --oneline -10
git status

# Verificar plan vigente
head -50 vultr-deploy-plan.md

# Preflight VPS Vultr (cuando IP exista)
bash scripts/vultr-preflight.sh

# Smoke test v1 stack (legacy, referencia)
bash scripts/smoke.sh
```

## Bloqueadores actuales

- Esperando IP VPS nuevo Santiago de operador
- Vultr API key quemada — rotar antes de cualquier automation
