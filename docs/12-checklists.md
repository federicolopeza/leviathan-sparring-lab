# 12 — Checklists + success criteria + cost

## Pre-deploy checklist

Antes de `./scripts/bootstrap.sh`:

```
[ ] BASE_DOMAIN decidido, zona Cloudflare activa
[ ] CF_API_TOKEN scoped a: Zone DNS + Zone WAF + Account Rulesets + Account Tunnel
[ ] VULTR_API_KEY generado (sub-account scoped al tag project=levlab si posible)
[ ] SSH key ED25519 generada + pubkey añadida al registry Vultr SSH Keys
[ ] WireGuard client pubkey lista; server keypair se genera en preflight
[ ] .env.lab completo desde .env.lab.example
[ ] RUN_ID asignado (default: YYYYMMDD-aN)
[ ] ground_truth.yml versión bumped si modificado
[ ] lab.yaml revisado (ROE)
[ ] Leviathan 8.2 build presente, /pentest + 9 skills específicos wired
[ ] Cloudflare Custom IP list ID registrado en .env.lab
[ ] Managed Rules + OWASP CRS PL2 enabled
[ ] Runner's egress IP(s) añadido a leviathan_runner_ips list
[ ] targets/lab/*/ Dockerfiles buildables locally (pre-cache bases caros)
[ ] Storage ≥ 10 GB free para artifacts
[ ] kill-switch roundtrip testeado en staging
[ ] 24h window reservada, operador disponible para Shell Gate / Phishing Gate
```

## Post-teardown checklist

Después de `./scripts/teardown.sh`:

```
[ ] artifacts exportados + hash-chain verificada
[ ] sha256sum manifests generados
[ ] docker compose down -v ejecutado
[ ] terraform destroy exitoso
[ ] vultr-cli instance list → cero levlab instances
[ ] Cloudflare DNS lab.* + *.lab.* records removidos
[ ] Cloudflare Tunnel credentials rotadas o deleted
[ ] Cloudflare IP list cleared o archivada
[ ] Ruleset disabled o archivada
[ ] WireGuard keys rotadas vía generate-wg-keys.sh --rotate
[ ] Grafana snapshots archivados a storage local
[ ] Wazuh / Suricata / Falco exports archivados
[ ] scoreboard.csv finalizado
[ ] postmortem.md completado con 11 secciones
[ ] Token economics (§11) computado desde cost-report.json
[ ] Tickets abiertos en arsenal/ para gaps encontrados
[ ] SBOM (leviathan-sbom.json) regenerado si deps cambiaron
```

## Success criteria

Antes de declarar "done":

```
[x] vultr-deploy-plan.md + docs/ completos
[ ] Repo scaffold materializado (Terraform + Ansible + 35 Dockerfiles + compose + scripts)
[ ] ground_truth/ground_truth.yml ≥ 100 entries (target 131)
[ ] terraform plan dry-run pasa
[ ] ansible-lint pasa
[ ] docker compose config validates
[ ] scripts/vultr-preflight.sh end-to-end
[ ] Deploy ejecutado → 28 stacks healthy en Traefik
[ ] wg0 up, public 22/80/443 cerrados, cloudflared conectado
[ ] Cloudflare allowlist + Managed Rules + OWASP CRS deployed
[ ] Wazuh + Suricata + Falco + Loki + Prometheus + Grafana ingesting live
[ ] /pentest STEALTH ≥ 10 findings, hash-chain intacta
[ ] Kill-switch validado hora 0
[ ] scripts/teardown.sh --dry-run pasa
[ ] Cost real reportado en postmortem
```

## Cost projection

### Infra 24h

| Item | Unit | Duración | Cost |
|---|---|---|---:|
| Vultr `vhp-8c-16gb-amd` | $0.143/h | 24h | **$3.43** |
| Bandwidth (2 TB peak) | $0.01/GB over included | ~0.1 TB over | **$0.60** |
| Cloudflare (free + WAF Managed) | $0 | 24h | **$0.00** |
| **Infra total** | | | **< $5** |

### Tokens Claude Opus (WARFARE heavy)

| Tier | Approx tokens | USD |
|---|---:|---:|
| STEALTH (1h, auto-chain 0) | 150K | $1-2 |
| TACTICAL (6h, 7 skills, auto-chain 2) | 900K | $3-5 |
| WARFARE (8h, auto-chain 4, swarm, deep+web hunter) | 2.5M | $8-15 |
| Chaos + analysis (4h) | 400K | $1-2 |
| **Token total** | **~4M** | **$13-24** |

### Total realístico por corrida

**$18-29 USD** — infra + tokens.

Operator ceiling mencionado era **< $10 infra** → CUMPLE ($5). Tokens son costo Opus separado — no parte del ceiling infra.

## Opciones cost reduction

Si operator quiere reducir más:

1. **STEALTH-only run** (no TACTICAL, no WARFARE) → ~$7 total
2. **TACTICAL-only run** (no WARFARE, no hunters) → ~$10 total
3. **Skip WARFARE hunters** (main pentest warfare OK, no /deep-hunter /web-hunter) → ~$18 total
4. **Haiku 4.5 para skills no-core** (`--model haiku` en /api-audit, /cloud-audit) → saves ~40% tokens pero -15% coverage
5. **Sampling**: corrida STEALTH completo + TACTICAL solo sobre 5 stacks muestra → $12 total, válido para smoke test framework

## Region selection

Default: `ewr` (Newark NJ). Alternativas:

| Region | Code | Notas |
|---|---|---|
| New York | ewr | Default, CF PoP NYC cerca |
| Los Angeles | lax | West Coast, CF PoP LAX |
| Miami | mia | Latencia Latam baja |
| Dallas | dfw | Central US |
| Frankfurt | fra | Europa, si operador EU |
| Singapore | sgp | APAC |

Misma tarifa en todos. Scaffold usa `ewr` default; operator cambia `VULTR_REGION` en `.env.lab`.

## Plan fallback

Si `vhp-8c-16gb-amd` unavailable en región:

| Plan | vCPU | RAM | Disk | $/h | Notas |
|---|---:|---:|---:|---:|---|
| vhp-8c-16gb-amd (preferred) | 8 | 16GB | 320GB NVMe | 0.143 | AMD EPYC |
| vc2-8c-16gb | 8 | 16GB | 160GB SSD | 0.144 | Intel, menos disk |
| vhp-6c-16gb-amd | 6 | 16GB | 240GB NVMe | 0.119 | Fallback budget |

Preflight valida + fallback automático.

## Hard limits para la corrida

```
max_runtime: 24h                  (ROE safety_limits)
max_rps_per_host: 20              (WARFARE tier)
max_concurrency: 12               (ROE)
max_auto_chain_depth: 4           (swarm = depth 4 × 3 parallel)
bandwidth_cap_warn: 2 TB          (vnstat cron cap warn)
bandwidth_cap_vultr: 3 TB         (provider hard cap)
operator_gate: shell + phishing   (ALWAYS ASK, no auto)
```

## Go/no-go final

**GO si:**
- Pre-deploy checklist 100%
- `scripts/vultr-preflight.sh` pasa
- Kill-switch test verde
- `scripts/smoke.sh` verde
- Operator disponible 24h

**NO-GO si:**
- Cualquier item pre-deploy no marcado
- Preflight reporta conflictos
- Smoke gate falla algún check
- Operador no puede estar disponible para Shell Gate / Phishing Gate eventos

NO-GO → fix + reintentar. No ejecutar benchmark sobre infra rota.
