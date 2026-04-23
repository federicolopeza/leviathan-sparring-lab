# 06 — Observability (defense telemetry)

Cámaras alrededor del ring. Todo lo que hace Leviathan queda grabado.

## Stack completo

```
Wazuh manager/indexer/dashboard    → SIEM central + SCA + FIM
Suricata (log-only)                → NIDS, EVE JSON
Falco (host)                       → runtime security kernel-level
Tetragon (k3s only)                → eBPF runtime in cluster
Arkime + tcpdump rolling           → pcap metadata + raw packets
Loki + Promtail + Grafana          → log aggregation + dashboards
Prometheus + node_exporter + cAdvisor → metrics + container stats
Cloudflare Logpush                 → edge WAF visibility
ModSecurity CRS wrappers           → per-stack WAF local
Local honeytokens                  → canary detection
```

## Filosofía de instrumentación

- **No mutar imágenes de terceros**
- Embedded agent **sólo** en imágenes propias (`lab/*`)
- Sidecar por namespace/red para imágenes de terceros
- Todo correlacionado con:

```yaml
labels:
  host: ${HOSTNAME}
  run_id: ${RUN_ID}
  stack: <service-name>
  chain: <leviathan_chain>
  tier: <stealth|tactical|warfare>
  source: <syslog|eve|modsec|falco|wazuh|cloudflare|app>
```

## Wazuh

Componentes:

```
wazuh.manager                      → decoder pipeline + rules engine
wazuh.indexer                      → OpenSearch fork, índice alerts
wazuh.dashboard                    → Kibana fork
wazuh-agent-*                      → embedded en imágenes propias, sidecar en terceros
```

Políticas:

- SCA Debian 12 CIS
- FIM en `/etc`, `/var/lib/docker`, `/opt/levlab`
- Decoders custom para:
  - Traefik access logs
  - ModSecurity audit logs
  - Suricata EVE JSON
  - Falco JSON
  - Arkime session metadata
  - Cloudflare Logpush

## Suricata log-only

Objetivo: **ver** todo, no bloquear.

Interfaces:
- `eth0` para tráfico host/wg/control
- Bridges Docker para HTTP east-west
- Opcional AF_PACKET `any` si aceptás ruido extra

`/etc/suricata/suricata.yaml`:

```yaml
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: /var/log/suricata/eve.json
      community-id: true
      types:
        - alert
        - http
        - dns
        - tls
        - files
        - flow
        - ssh
        - smtp
        - stats

rule-files:
  - suricata.rules
```

```bash
suricata-update
systemctl enable --now suricata
```

## Arkime + tcpdump rolling

Captura:

- tcpdump ring buffer → raw pcap: 96 ficheros × 15 min = 24h
- Arkime → metadata + sesiones + búsqueda

`/usr/local/sbin/pcap-ring.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
mkdir -p /pcap/ring
exec tcpdump -i any -s 0 -C 256 -W 96 -w /pcap/ring/levlab-%Y%m%d%H%M%S.pcap \
  not host 127.0.0.1
```

Systemd unit con `NoNewPrivileges=true`, `RestrictAddressFamilies`, etc.

## Loki + Promtail + Grafana

Promtail scrapea:

- `/var/log/syslog`
- `/var/log/auth.log`
- `/var/log/suricata/eve.json`
- `/var/log/modsec/*.log`
- `/var/log/traefik/access.log`
- `/var/log/falco/falco.log`
- Wazuh archive alerts
- cloudflared logs
- app logs etiquetados por stack

## Prometheus + exporters

Targets:
- Host CPU/mem/disk/net (node_exporter)
- Docker stats por contenedor (cAdvisor)
- cloudflared metrics (`127.0.0.1:60123`)
- Traefik metrics
- Grafana/Loki health
- Tetragon metrics
- Falco exporter (opcional)
- Wazuh dashboard/indexer health

## ModSecurity CRS delante de cada stack

```
Cloudflare Edge WAF
  └─► cloudflared
      └─► traefik
          └─► modsec-<stack> (owasp/modsecurity-crs)
              └─► app
```

Ventajas:
- WAF real en edge (mide Leviathan contra Cloudflare)
- WAF local con audit logs ricos por stack
- Sin depender de Traefik plugins runtime

Imagen: `owasp/modsecurity-crs:nginx`. Paranoia `PL2`, audit log rotated.

## Runtime security

**Falco** — host-wide, reglas default + custom para el lab.
**Tetragon** — solo dentro de k3s (TracingPolicies + Prometheus metrics).

## Honeytokens

Plantados por Ansible role `honeytokens`:

| Path | Tipo | Trigger |
|---|---|---|
| `/etc/levlab-canary/root_token.txt` | file | auditd watch |
| `/var/lib/postgresql/data/canary_customers.csv` | DB row | pg_audit |
| MinIO `finance-private/payroll-2026.csv` | bucket object | MinIO access log |
| Vault `prod/github_pat` | secret | Vault audit log |
| Jenkins `$JENKINS_HOME/secrets/master.key.copy` | file | AIDE FIM |
| Gitea repo `platform/dev-platform/.env.production.bak` | git file | Gitea webhook on clone |

Triggers route a Wazuh via custom decoders → Grafana dashboard "CVE / GT hits".

## 8 Grafana dashboards pre-provisioned

1. **Payloads received per stack** — Traefik access + ModSec audit + Suricata HTTP
2. **CVE hits / GT hits** — Leviathan findings + Wazuh custom index
3. **Auth failures per stack** — auth.log + app logs + Keycloak/GitLab/Jenkins/Dovecot
4. **Privilege escalation attempts** — Falco + auditd execve + Tetragon
5. **Lateral movement indicators** — pivot_net flows + SMB/LDAP/k8s token usage + credential reuse
6. **WAF interaction panel** — Cloudflare action + ModSec action + Suricata SID + response code
7. **Time-to-first-critical** — query `leviathan_findings{severity="critical"}` min(ts)
8. **Evidence chain health** — hash-chain append rate + missing segments + `verify_chain` result

Dashboards committed como JSON en `ansible/files/grafana/dashboards/*.json`. Provisioning API los carga al startup.

## Smoke test — GATE bloqueante

**Antes del benchmark kickoff, 8 checks obligatorios.** Si alguno falla → kickoff bloqueado.

`scripts/smoke.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

HOSTS=(lab.${BASE_DOMAIN} wp.lab.${BASE_DOMAIN} ...)

# 1. Todos los Traefik routers responden 2xx/3xx
for h in "${HOSTS[@]}"; do
  code=$(curl -sk --max-time 15 -o /dev/null -w '%{http_code}' "https://$h")
  [[ "$code" =~ ^[23] ]] || fail "$h → $code"
done

# 2. Wazuh recibió ≥1 evento de ≥1 stack en <5min
wazuh_count=$(curl -sku admin:admin \
  "https://wazuh-manager:55000/security/alerts?limit=1" | jq '.data.total_alerts')
[[ $wazuh_count -gt 0 ]] || fail "Wazuh ingesting 0 events"

# 3. Suricata eve.json tiene ≥1 línea
[[ $(wc -l </var/log/suricata/eve.json) -gt 0 ]] || fail "Suricata silent"

# 4. Falco JSON heartbeat activo (log en últimos 60s)
last_falco=$(stat -c %Y /var/log/falco/falco.log)
[[ $(( $(date +%s) - last_falco )) -lt 120 ]] || fail "Falco stale"

# 5. Loki acepta push + query funciona
resp=$(curl -s "http://loki:3100/loki/api/v1/query?query=%7Brun_id%3D%22$RUN_ID%22%7D")
echo "$resp" | jq -e '.status == "success"' >/dev/null || fail "Loki query fail"

# 6. Grafana dashboards + datasources healthy
for ds in loki prometheus wazuh; do
  curl -sku admin:$GF_PASS "http://grafana:3000/api/datasources/name/$ds/health" \
    | jq -e '.status == "OK"' >/dev/null || fail "Grafana $ds unhealthy"
done

# 7. Cloudflare Logpush endpoint alcanzable
curl -sk --max-time 10 -X POST "https://logpush.${BASE_DOMAIN}/test" -d '{"test":1}' \
  | grep -q '"ok":true' || fail "CF Logpush endpoint down"

# 8. Kill-switch roundtrip
touch /opt/levlab/KILL_SWITCH
sleep 2
curl -sk "https://lab.${BASE_DOMAIN}/kill-switch" | grep -q "503" || fail "Kill-switch broken"
rm /opt/levlab/KILL_SWITCH

echo "[OK] 8/8 smoke checks passed. Kickoff permitted."
```

Falla → dump `journalctl -u docker --since -30m` + `docker compose ps` → abort. Operador ve error; fix antes de kickoff.

## Por qué smoke test como gate

Correr benchmark sobre observabilidad rota = datos basura. Si Wazuh no ingesta o Falco está muerto, las métricas defensivas son fantasía. Gate duro previene eso.
