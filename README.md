# Leviathan Sparring Lab

Benchmark empírico efímero de **Leviathan 8.2** contra zoo de 28 apps vulnerables. VPS Vultr, 24h, destroy-after, <$5 USD infra.

## Qué es

Gimnasio de boxeo alquilado por 24h. Leviathan (boxeador) pega contra 28 sacos vulnerables. Cámaras (Wazuh/Suricata/Falco/Grafana) graban todo. Al final se mide recall, precision, WAF bypass, token economics.

Explicación completa: [docs/00-overview.md](docs/00-overview.md).

## Quick start

```bash
git clone <this-repo>
cd leviathan-sparring-lab/

# 1. Llenar credenciales
cp .env.lab.example .env.lab
vim .env.lab                      # Vultr API, Cloudflare token, dominio, etc.

# 2. Deploy end-to-end (30 min)
./scripts/bootstrap.sh

# 3. Kickoff benchmark desde Leviathan CLI
/pentest https://lab.${BASE_DOMAIN} --roe lab.yaml --mythos stealth --auto-chain 0

# 4. Después de 24h
./scripts/teardown.sh
```

## Docs

| # | Archivo | Para |
|---|---|---|
| 00 | [overview](docs/00-overview.md) | Primera lectura — explicación fácil |
| **INFRA** — lo que se construye antes de arrancar | | |
| 01 | [architecture](docs/01-architecture.md) | Topología red + Vultr edge cases |
| 02 | [infrastructure](docs/02-infrastructure.md) | Terraform Vultr + repo layout + Makefile |
| 03 | [hardening](docs/03-hardening.md) | OS hardening + Docker + firewall + kill-switch |
| 04 | [zoo-targets](docs/04-zoo-targets.md) | 28 stacks + seeded CI/CD repos |
| 05 | [ground-truth](docs/05-ground-truth.md) | 131 entries esperadas |
| 06 | [observability](docs/06-observability.md) | Wazuh/Suricata/Falco/Grafana + smoke gate |
| **LEVIATHAN** — lo que ejecuta durante 24h | | |
| 07 | [roe](docs/07-roe.md) | lab.yaml + Mythos tiers + auto-chain |
| 08 | [runbook](docs/08-runbook.md) | 7 ventanas hora-por-hora |
| 09 | [metrics-scoring](docs/09-metrics-scoring.md) | Scoreboard + coverage + FP rate |
| 10 | [postmortem](docs/10-postmortem.md) | Template informe + token economics |
| **OPS** — scripts y checklists | | |
| 11 | [operations](docs/11-operations.md) | Bootstrap/teardown/kill/export |
| 12 | [checklists](docs/12-checklists.md) | Pre/post + success criteria + cost |
| 13 | [credentials-guide](docs/13-credentials-guide.md) | Cómo obtener + dónde guardar cada credencial |

## Status

- Plan documental: **completo** (14 archivos en `docs/`)
- Repo scaffold (Terraform + Ansible + Dockerfiles + compose): **pendiente**
- VPS Vultr: **pendiente** (operador crea cuando quiera)
- Benchmark ejecutado: **pendiente** (24h window post-scaffold+deploy)

## Costo

- Infra 24h: **< $5 USD**
- Tokens Claude Opus: $13-24 USD (WARFARE heavy)
- Total realístico: **$18-29 USD** por corrida completa

Detalle: [docs/12-checklists.md#cost-projection](docs/12-checklists.md#cost-projection).

## Stack

- **Provider:** Vultr (`vx1-g-8c-32g-480s`, 8 vCPU / 32 GB / 480 GB NVMe, ~$7.34/24h)
- **OS:** Debian 12 minimal
- **Runtime:** Docker 26 + userns-remap + seccomp + AppArmor
- **Ingress:** Cloudflare Tunnel (`cloudflared`) + Traefik + ModSec CRS
- **Management:** WireGuard wg0
- **IaC:** Terraform (`vultr/vultr ~>2.21`) + Ansible 9 roles
- **Defense:** Wazuh + Suricata + Falco + Loki + Prometheus + Grafana + Arkime
- **Offense:** Leviathan 8.2 (285 módulos, 122 MCP tools, 28 chains, Mythos STEALTH/TACTICAL/WARFARE, auto-chain tier 0-4 + swarm)

## Safety

- ROE-gated toda acción (scope, deny_actions, safety_limits)
- Operator Shell Gate + Phishing Gate siempre ask
- Kill-switch wireado (file + HTTP, 503 response, middleware check)
- Hash-chain evidence — teardown aborta si chain rota
- Destroy-after genuino — Vultr resource verify = 0 post-destroy

## Requisitos operador

- Cuenta Vultr con API key
- Dominio con zona Cloudflare activa + API token (Zone DNS + WAF + Tunnel + Rulesets)
- SSH key ED25519
- WireGuard client instalado laptop
- 24h disponibilidad para Shell/Phishing gates

## Licencia

Interno. No publicar.
