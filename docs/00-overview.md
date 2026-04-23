# 00 — Overview (explicación fácil)

## Qué es esto

Un benchmark empírico de **Leviathan 8.2** (framework pentest autónomo, 285 módulos, 122 MCP tools, 28 attack chains) contra un laboratorio efímero de 24h con 28 apps deliberadamente vulnerables.

**Propósito:** medir si Leviathan sirve de verdad. Recall, precision, WAF bypass, Mythos tiers, chains cross-stack.

## Analogía

Gimnasio de boxeo alquilado 24h.

- **Vultr VPS** = gimnasio (alquilás, usás, devolvés)
- **28 apps rotas** = sacos de boxeo (WordPress 5.0.0 con CVE, Jenkins 2.0, MinIO mal configurado, etc.)
- **Leviathan** = boxeador
- **Wazuh + Suricata + Falco + Grafana** = cámaras de seguridad alrededor del ring
- **24h timer** = barato ($5 infra) + reproducible desde cero + cero rastro

Leviathan pega 24h. Cámaras graban todo. Al final medís: cuántos sacos rompió / cuánto ruido hizo / cuánto costó.

## Truco arquitectónico

**Hardened afuera, vulnerable adentro.** Cloudflare + WAF + firewall paranoico por fuera (parece target real). Apps rotas a propósito por dentro. Leviathan tiene que:

1. Pasar Cloudflare Managed Rules + OWASP CRS PL2
2. Pasar allowlist de IP
3. Pasar rate limits
4. Después explotar las apps internas

Eso te da métricas reales, no laboratorio de cartón.

## Flujo 24h

| Hora | Fase | Qué hace |
|---|---|---|
| 0-1 | Deploy | Terraform + Ansible + docker compose + smoke test (gate) |
| 1-2 | STEALTH | Recon silencioso. Mido ruido mínimo |
| 2-8 | TACTICAL | Ataque normal. 9 skills Leviathan en paralelo |
| 8-16 | WARFARE | Todo a fondo. Swarm Opus + deep-hunter + web-hunter + source-audit |
| 16-20 | Chaos | Reutilizo credenciales, pivot lateral controlado |
| 20-23 | Análisis | Exporto artifacts, construyo scoreboard, cruzo con ground truth |
| 23-24 | Teardown | Destroy VPS, verify hash-chain, rotate keys |

## Resultado

`postmortem.md` con:

- Coverage: 118/131 vulns detectadas (90%)
- FP rate por skill
- WARFARE vs TACTICAL: vale el costo extra? (token economics)
- Chains cross-stack que funcionaron
- Gaps → tickets para `arsenal/`

## Por qué partimos el plan en docs/

Plan monolítico de 1690 líneas mezclaba:
- Infra (Terraform, Cloudflare, firewall)
- Leviathan (ROE, runbook, scoring)
- Ops (scripts, checklists)

Imposible de revisar en partes. Ahora está dividido:

```
docs/
├── 00-overview.md              # este archivo
├── 01-architecture.md          ┐
├── 02-infrastructure.md        │  INFRA — lo que Claude construye
├── 03-hardening.md             │  antes de que Leviathan arranque
├── 04-zoo-targets.md           │
├── 05-ground-truth.md          │
├── 06-observability.md         ┘
├── 07-roe.md                   ┐
├── 08-runbook.md               │  LEVIATHAN — lo que ejecuta
├── 09-metrics-scoring.md       │  durante las 24h
├── 10-postmortem.md            ┘
├── 11-operations.md            ┐  OPS — scripts y checklists
└── 12-checklists.md            ┘  que pegan todo
```

## Quién lee qué

| Rol | Lee | Salto |
|---|---|---|
| Operador primera vez | 00 → 12 → 08 | 5 min |
| Claude (tú, ahora) ejecutando scaffold | 01-06 | fase construcción |
| Leviathan (framework) ejecutando benchmark | 07-10 | fase runtime |
| Operador día de corrida | 11 + 12 | scripts + checklists |
| Debugger post-mortem | 09 + 10 | métricas + informe |

## Estado actual

- Plan documental: **completo** (este docs/)
- Repo scaffold: **pendiente** (~60 archivos: Terraform/Ansible/Dockerfiles/compose/scripts)
- VPS Vultr: **pendiente** (operador crea cuando quiera)
- Benchmark ejecutado: **pendiente** (24h después de scaffold+deploy)

## Costo

- Infra 24h: **< $5 USD** ($3.43 Vultr + ≤$0.60 bandwidth + $0 Cloudflare)
- Tokens Claude Opus (WARFARE heavy): **$8-20 USD** (separado, medido en [postmortem §11](10-postmortem.md#11-token-economics))
- Total realista: **< $25 USD** por corrida completa

## Próximo paso

Cuando digas "scaffold" → materializo los ~60 archivos (Terraform + Ansible + 35 Dockerfiles + compose + scripts). Después operador da IP VPS + dominio → deploy.
