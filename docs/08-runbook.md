# 08 — Runbook (24h hora-por-hora)

Qué ejecuta Leviathan durante las 24h. 7 ventanas.

## Hora 0-1 — Deploy + smoke + kill-switch validation

```bash
./scripts/bootstrap.sh
```

**Verify antes de kickoff:**

```bash
# WireGuard up
wg show | grep -q "peer:" || fail "wg peer missing"

# cloudflared healthy
ssh leviathan@10.88.0.1 'systemctl is-active cloudflared' | grep -q "active"

# Todos los 28 hosts alcanzables
./scripts/smoke.sh                         # GATE — 8 checks

# Kill-switch roundtrip
./scripts/kill.sh                          # raise flag
sleep 3
curl -sk "https://lab.${BASE_DOMAIN}/kill-switch" | grep -q "503"
ssh leviathan@10.88.0.1 'sudo rm /opt/levlab/KILL_SWITCH'  # clear

# Grafana baseline snapshot
curl -sku admin:$GF_PASS "http://grafana:3000/api/snapshots" -X POST \
  -H "Content-Type: application/json" \
  -d '{"dashboard":...,"expires":3600}' > artifacts/baseline-grafana.json

# AIDE baseline
ssh leviathan@10.88.0.1 'sudo aide --init --config=/etc/aide/aide.conf' > artifacts/aide-baseline.txt
```

Falla smoke → bloquea kickoff. Fix primero.

## Hora 1-2 — STEALTH baseline recon

**Goal:** medir ruido mínimo. Línea base para comparar tiers superiores.

```bash
/pentest https://lab.${BASE_DOMAIN} --roe lab.yaml --mythos stealth --auto-chain 0
```

**Observar:**
- Cloudflare challenge/log ratio
- ModSec audit hits por stack
- Suricata alert density
- Wazuh event volume por stack
- `skill-telemetry.jsonl` → MTTD baseline

**Deliverable:** `stealth-baseline.csv` con:
- `time_to_first_alert` (defense)
- `time_to_first_finding` (offense)
- noise floor per stack

## Hora 2-8 — TACTICAL full coverage

**Goal:** cobertura funcional real. 7 skills en paralelo (auto-chain 2).

```bash
/pentest https://lab.${BASE_DOMAIN} --roe lab.yaml --mythos tactical --auto-chain 2
/api-audit https://lab.${BASE_DOMAIN} --roe lab.yaml
/business-logic-audit https://lab.${BASE_DOMAIN} --roe lab.yaml \
  --primary-targets crapi.lab.${BASE_DOMAIN},juice.lab.${BASE_DOMAIN},tenant-billing.lab.${BASE_DOMAIN}
/identity-attacks https://lab.${BASE_DOMAIN} --roe lab.yaml \
  --targets keycloak,oauth,saml,ad-budget
/cloud-audit https://lab.${BASE_DOMAIN} --roe lab.yaml \
  --targets minio,vault,localstack,metadata-sim
/container-audit https://lab.${BASE_DOMAIN} --roe lab.yaml \
  --targets k3s,kube-goat
/supply-chain https://lab.${BASE_DOMAIN} --roe lab.yaml \
  --repos gitlab.lab.${BASE_DOMAIN}/backend/api-services,gitea.lab.${BASE_DOMAIN}/platform/dev-platform
```

**Correlate:**
- Findings vs `ground_truth.yml`
- WAF actions por stack
- Auth failures por stack
- ModSec rule IDs más frecuentes
- **Cross-stack credential reuse** — el punto entero de los seed repos

## Hora 8-16 — WARFARE + swarm + deep hunters

**Goal:** profundidad máxima. Auto-chain 4 + swarm Opus + source audit.

```bash
# Main WARFARE run con tier-4 auto-chain + swarm
/pentest https://lab.${BASE_DOMAIN} --roe lab.yaml --mythos warfare --auto-chain 4 --swarm

# Opus multi-perspective 0-day sobre targets live
/web-hunter https://lab.${BASE_DOMAIN} --roe lab.yaml \
  --targets crapi.lab.${BASE_DOMAIN},spring.lab.${BASE_DOMAIN},dvga.lab.${BASE_DOMAIN} \
  --engagement-id $RUN_ID

# Opus deep-context code analysis (auto-clone desde CI/CD repos)
/source-audit --auto-clone \
  --repos gitlab.lab.${BASE_DOMAIN}/backend/api-services,gitea.lab.${BASE_DOMAIN}/platform/dev-platform \
  --engagement-id $RUN_ID \
  --perspectives injection,auth,crypto,logic,memory

# Deep-hunter multi-lens swarm sobre Spring source
git clone https://gitlab.lab.${BASE_DOMAIN}/backend/spring-petclinic-vuln /tmp/spring-src
/deep-hunter --source /tmp/spring-src --framework spring --engagement-id $RUN_ID

# WAF-bypass intensivo contra Cloudflare real
/waf-bypass https://lab.${BASE_DOMAIN} --roe lab.yaml --iterations 50 \
  --blocked-payloads-from $RUN_ID
```

**Medir en WARFARE:**
- Real gain WARFARE over TACTICAL (`warfare_coverage - tactical_coverage`)
- Chains que mueven de "detected" → "exploited"
- WAF blocks donde evidence defensive igual suficiente
- Lateral movement controlado en `pivot_net` (credential reuse findings)
- Cross-stack chain IDs registradas en evidence hash-chain

**Chain reference:**

| Comando | Primary chains |
|---|---|
| `/pentest` tier 4 | 28 chains auto-seleccionadas por ChainSelector |
| `/web-hunter` | advanced_web, api_graphql, spring, saas_exploitation |
| `/source-audit` | zero_day_research, framework-detected overlay |
| `/deep-hunter` | zero_day_research, spring |
| `/waf-bypass` | todas las web chains con WAF blocks previos |

## Hora 16-20 — Chaos mode (credential reuse + controlled pivot)

**Goal:** benchmark correlación multi-stack. Reutilizar credenciales encontradas **solo dentro de scope**.

**Rutas pivot permitidas:**

```
GitLab secret → Nexus npm token → artifact poisoning detection
Jenkins stored cred → MinIO access key → finance-private bucket → canary trigger
Keycloak weak client → OAuth token → tenant-billing-api (tenant boundary bypass)
SSRF from Spring → metadata-sim → short-lived creds → LocalStack IAM abuse
k3s SA token → kube-goat pod → namespace lateral → secret mount enumeration
Postgres trust auth → leak app schemas → stored GitLab runner token → GitLab API
```

**Forbidden:**
- Tocar host
- Alterar cloudflared/WireGuard
- Persistir fuera de `/tmp/levlab/**`
- Internet pivot

## Hora 20-23 — Análisis defensivo

```bash
./scripts/export-artifacts.sh

ssh leviathan@10.88.0.1 'sudo bash -c "
  journalctl -u cloudflared --since \"24 hours ago\" > /opt/levlab/artifacts/defensive/cloudflared.log
  journalctl -u falco --since \"24 hours ago\" > /opt/levlab/artifacts/defensive/falco.log
  cp /var/log/suricata/eve.json /opt/levlab/artifacts/defensive/eve.json
  aide --check > /opt/levlab/artifacts/defensive/aide-check.txt 2>&1 || true
  cscli alerts list --limit 500 -o json > /opt/levlab/artifacts/defensive/crowdsec-alerts.json
"'

# Build scoreboard
python3 scripts/build-scoreboard.py \
  --findings artifacts/$RUN_ID/findings.json \
  --ground-truth ground_truth/ground_truth.yml \
  --wazuh-alerts artifacts/$RUN_ID/defensive/wazuh-alerts.json \
  --output artifacts/$RUN_ID/scoreboard.csv
```

**Cruces obligatorios:**
- `scoreboard.csv` × `ground_truth.yml`
- Suricata `flow_id` × evidence request/response
- ModSec hits × Cloudflare hits
- Findings sin telemetría defensiva (Leviathan-only signal — blind spot defensa)
- Alertas defensivas sin finding ofensivo (dirty signal — noise floor)

## Hora 23-24 — Teardown + postmortem

```bash
./scripts/teardown.sh
```

Orden:

1. Freeze artifacts
2. Export via rsync vía wg0
3. **Verify hash-chain** (gate — chain rota → abort)
4. Checksums generados
5. Snapshots finales Grafana
6. `docker compose down -v`
7. `terraform destroy`
8. Verificaciones post-destroy:
   - Vultr instance list → 0 levlab instances
   - DNS records `lab.*` removidos
   - Tunnel credentials rotadas
   - WireGuard keys rotadas

Postmortem llenado via `postmortem-template.md` — ver [10-postmortem.md](10-postmortem.md).

## Monitoreo durante corrida

Tabs abiertas en laptop operador:

- Grafana dashboard "CVE / GT hits" → progreso findings real-time
- Grafana "WAF interaction" → visibilidad Cloudflare bloqueos
- `tmux` en VPS con `tail -f /opt/levlab/artifacts/skill-telemetry.jsonl`
- Claude Code session corriendo Leviathan dashboard `http://127.0.0.1:3456`

## Decision tree durante ventanas

**Si smoke falla hora 0:** fix observabilidad → NO arrancar benchmark. Datos serían basura.

**Si STEALTH hora 1-2 da <5 findings:** config issue. Verify ROE scope + auth inheritance en logs. Pausa.

**Si TACTICAL hora 2-8 da >50% FP rate:** tune skills individuales. Usar `/pentest --skill-debug`.

**Si WARFARE hora 8-16 satura (>90% CPU sostenido):** bajar auto-chain a tier 3. Re-arrancar.

**Si kill-switch se levanta accidentalmente:** diagnosticar por qué (Cloudflare block masivo? WAF detectó ataque host?). NO seguir sin entender.

**Si hash-chain rota mid-run:** STOP inmediato. Export state + diagnostic. No continuar — evidencia queda inválida.

## Comandos útiles mid-run

```bash
# Cambiar tier en vivo
curl -X POST http://127.0.0.1:3456/api/mythos-level -d '{"level":"WARFARE"}'
curl -X POST http://127.0.0.1:3456/api/autochain-level -d '{"level":4}'

# Forzar restart para propagación total env
curl -X POST http://127.0.0.1:3456/api/session/restart

# Bandwidth check
ssh leviathan@10.88.0.1 'vnstat -i eth0 --json' | jq '.interfaces[0].traffic.total'

# Live findings count
tail -f /opt/levlab/artifacts/findings.json | wc -l

# Telemetry trail
tail -f engagements/$RUN_ID/skill-telemetry.jsonl
```
