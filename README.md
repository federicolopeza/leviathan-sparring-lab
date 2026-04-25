# Leviathan Sparring Lab — v2

Lab pentest **persistente y leveable** sobre Vultr Santiago. 6 containers core + GT rotator on-demand. Hardening defensivo épico para que cada finding atacante sea ganado, no regalado.

**Targets:**
- Engagement Gonxa (blackbox `melispy.com`)
- Corridas internas Leviathan (benchmark vs GT rotativo)
- Sparring partner para training defensivo

## Status

- Plan v2: ✅ [vultr-deploy-plan.md](vultr-deploy-plan.md) — source of truth
- Reorg repo: ⏳ en transición v1 → v2
- VPS Santiago: ⏳ pending deploy
- Bootstrap: ⏳ pending IP nuevo

Detalle: [HANDOFF.md](HANDOFF.md).

## Quick start (v2 — ETA cuando bootstrap esté listo)

```bash
git clone <this-repo>
cd leviathan-sparring-lab/

# 1. Credenciales
cp .env.lab.example .env.lab
$EDITOR .env.lab  # Vultr API, CF token, CF zone, CF tunnel, base_domain

# 2. Deploy VPS + bootstrap (~15 min)
bash scripts/lab-up.sh

# 3. WireGuard handshake (única vez)
sudo wg-quick up engagements/wg-client.conf

# 4. Activar primer GT
bash scripts/gt-rotate.sh dvwa

# 5. Stack up
ssh levlab "cd lab && docker compose -f docker-compose.lean.yml up -d"

# 6. Verify defensa
bash scripts/waf-test.sh
ssh levlab "sudo lynis audit system" | grep "Hardening index"
```

Tear down (vuelve a snapshot, libera VPS):
```bash
bash scripts/lab-down.sh
```

## Stack v2

### Core (6 containers, siempre on)

| Container | Rol |
|---|---|
| `cloudflared` | Tunnel (cero IP pública entrante) |
| `traefik` | TLS interno + routing + middleware |
| `kali` | Toolkit attacker side (uso interno) |
| `metasploit` | Exploitation framework |
| `gt-active` | Slot único — GT del momento, swap via rotator |
| `loki` + promtail | Logs centralizados |

### Opt-in (compose profiles)

| Container | Rol |
|---|---|
| `falco` | Runtime detection anti-Gonxa TTPs |
| `crowdsec` | Community blocklist + bouncer |
| `honeypot-cowrie` | SSH honeypot trap |
| `grafana` | Dashboards Loki (on-demand only) |

### Catálogo GT (no runtime)

37 stacks Dockerfileados en `targets/`. Solo 1-2 activos vía `gt-rotate.sh`. Lista: ver `targets/catalog.yml` (pendiente).

## Defensa-en-profundidad

**Anti-recon:**
- DNS sin wildcard, CT pruning, Tunnel ingress explícito por hostname
- WAF custom rules bloquean scanner UAs default

**Anti-attack:**
- Cloudflare WAF active (no log) + OWASP CRS PL2 + Bot Fight + JA3/JA4
- Rate limit 50 rps/IP, escala a challenge
- CrowdSec community blocklist + bouncer Traefik
- Fail2ban jails SSH/Traefik/auth

**Container hardening:**
- userns-remap, seccomp, AppArmor, cap_drop ALL, read_only, no-new-privileges, non-root user, pinned digests, trivy scan

**Network isolation:**
- 3 docker networks (mgmt/attacker/target). `target_net` internal, sin egress salvo whitelist
- WG peer único (laptop operador), SSH solo via WG post-bootstrap

**Detection:**
- Falco runtime + custom rules anti-Gonxa
- AIDE FIM + cron diario
- Loki centralizado: SSH auth, sudo, docker events, WAF blocks, fail2ban, falco

Detalle full: [vultr-deploy-plan.md](vultr-deploy-plan.md) sección "Hardening checklist (épico)".

## Costo

| Modo | $/mo |
|---|---|
| Ephemeral (4-6h/día) | ~$5 |
| 24/7 persistente | ~$25 |
| Engagement Gonxa 24h | ~$0.79 (VPS) + tokens Opus |

## Docs

| # | Archivo | Status v2 |
|---|---|---|
| 00 | [overview](docs/00-overview.md) | ⏳ re-scope |
| 01 | [architecture](docs/01-architecture.md) | ⏳ re-scope (3 nets vs 12) |
| 02 | [infrastructure](docs/02-infrastructure.md) | ⏳ re-scope (CF-only ya, lean) |
| 03 | [hardening](docs/03-hardening.md) | ⏳ EXPAND con checklist v2 |
| 04 | [zoo-targets](docs/04-zoo-targets.md) | ⏳ rename → `04-targets-catalog.md` |
| 05 | [ground-truth](docs/05-ground-truth.md) | ✅ vigente, +flag `active_in_lab` |
| 06 | [observability](docs/06-observability.md) | ⏳ recortar a Loki + opt-ins |
| 07 | [roe](docs/07-roe.md) | ✅ vigente |
| 08 | [runbook](docs/08-runbook.md) | ⏳ re-scope ops cotidiano |
| 09 | [metrics-scoring](docs/09-metrics-scoring.md) | ⏳ EXPAND métricas defensivas |
| 10 | [postmortem](docs/10-postmortem.md) | ✅ vigente |
| 11 | [operations](docs/11-operations.md) | ⏳ re-scope scripts nuevos |
| 12 | [checklists](docs/12-checklists.md) | ⏳ re-scope v2 |
| 13 | [credentials-guide](docs/13-credentials-guide.md) | ⏳ +WG keys, +B2 |
| 14 | defense-playbook | ⏳ NEW (anti-recon + IR) |

## Stack tecnológico

- **VPS:** Vultr `vhp-2c-4gb-amd` Santiago CL
- **OS:** Debian 12 minimal
- **Runtime:** Docker 26 + userns-remap + seccomp + AppArmor
- **Ingress:** Cloudflare Tunnel + WAF active + Traefik v3
- **Mgmt:** WireGuard wg0 (peer único)
- **IaC:** Terraform CF-only (Vultr manual UI) + Ansible roles slim
- **Defense runtime:** Loki+Promtail core; Falco/CrowdSec/AIDE opt-in
- **Offense (interno):** Leviathan 8.2 + Burp (laptop) + Metasploit + Kali toolkit

## Safety

- ROE-gated por engagement (`lab.yaml` por run)
- Operator Shell Gate + Phishing Gate siempre ask
- Hash-chain evidence + verify pre/post run
- Snapshot pre-engagement como safety net (rollback si breakout)
- Destroy genuino — Vultr resource verify = 0 post-destroy

## Requisitos operador

- Cuenta Vultr con API key (rotada)
- Zona Cloudflare activa `melispy.com` + API token
- SSH key ED25519
- WireGuard client laptop
- Git Bash o equivalente Unix shell

## Licencia

Interno. No publicar.
