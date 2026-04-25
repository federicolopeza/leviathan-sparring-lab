# Legacy v1 — Archivo histórico

Estos archivos pertenecen al plan v1 (28-stack ephemeral 24h benchmark) y fueron movidos al reorg v2 (2026-04-25).

**No usar para deploys nuevos.** Conservados como referencia y para rollback de emergencia.

## Contenido

| File/dir | Descripción |
|---|---|
| `docker-compose.yml` | 1067 líneas, 28 target stacks + observability completa (Wazuh/Suricata/Falco/Tetragon/Arkime/etc) |
| `docker-compose.prod.yml` | 551 líneas, 22 stacks variant upstream-only |
| `ansible/` | 9 roles para v1 (cloudflared, docker, hardening, honeytokens, kill-switch, observability, seed-cicd-repos, wireguard, zoo-deploy) |
| `bootstrap.sh` | Pipeline 30-min: terraform apply → cloud-init wait → ansible → compose up → smoke gate |
| `teardown.sh` | 24h destroy-after: export artifacts → compose down → terraform destroy → CF cleanup → WG rotation |
| `Makefile` | Targets v1 (preflight/apply/ansible/up/down/destroy/smoke) |

## Por qué se movió

v2 cambia de:
- Benchmark 24h destroy-after → lab persistente / ephemeral on-demand
- Terraform Vultr → manual UI (Terraform CF-only)
- 28 stacks live → 6 core + GT rotator
- Observability heavy → Loki+Promtail core + opt-ins

Detalle full: [`vultr-deploy-plan.md`](../vultr-deploy-plan.md) sección "Cambios vs v1".

## Cuando borrar definitivamente

Tras 2-3 corridas exitosas v2 (Gonxa engagement + Leviathan benchmark):
```bash
git rm -rf legacy/
git commit -m "remove v1 legacy after v2 stabilized"
```

## Reusables extraídos antes del move

Scripts v2 derivan o reusan ideas de:
- `bootstrap.sh` → `scripts/lab-up.sh` (sin terraform Vultr)
- `teardown.sh` → `scripts/lab-down.sh` (con snapshot+destroy lifecycle)
- `ansible/roles/hardening/` → `scripts/harden.sh` (idempotent script único)
- `ansible/files/seccomp/levlab-default.json` → reusar en `docker-compose.lean.yml`
- `ansible/files/grafana/dashboards/*.json` → opcional importar a Grafana v2
- `Makefile` → reescrito slim
