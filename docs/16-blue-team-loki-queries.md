# 16 — Blue-Team Loki Query Pack (attacker tracking)

**Audience:** operador (vos) durante engagement.
**Purpose:** queries listas para Grafana (cuando levantes profile `dashboards`) o `logcli` desde laptop con WireGuard.

---

## Setup Grafana (on-demand)

```bash
ssh root@64.176.15.72 "cd /opt/levlab && docker compose -f docker-compose.lean.yml --env-file .env.lab --profile dashboards up -d grafana"
# Acceso vía CF Tunnel (whitelisted operator IP):
# https://grafana.melispy.com  (admin / $GRAFANA_ADMIN_PW)
# Datasource: http://loki:3100 (http URL, in-cluster)
```

---

## Honeypot — alta señal scanner / recon

### Total honeypot hits últimos 5min
```logql
sum(count_over_time({container="levlab-gt-honeypot"} |~ "WARNING|category" [5m]))
```

### Top categorías de probes
```logql
topk(10, sum by (category) (count_over_time({container="levlab-gt-honeypot"} | json msg | line_format "{{.msg}}" | json | __error__="" [1h])))
```

### Hits por categoría high/critical
```logql
{container="levlab-gt-honeypot"}
  | json msg
  | line_format "{{.msg}}"
  | json
  | severity =~ "high|critical"
  | line_format "[{{.category}}] {{.path}} from {{.src}} (UA: {{.ua}}, trace={{.trace}})"
```

### Trace ID — agrupar por sesión atacante
```logql
{container="levlab-gt-honeypot"}
  | json msg
  | line_format "{{.msg}}"
  | json
  | trace="0c433f05e4f1"
```

### IP que más toca honeypot (top atacantes)
```logql
topk(10, sum by (src) (count_over_time({container="levlab-gt-honeypot"} | json msg | line_format "{{.msg}}" | json | __error__="" [1h])))
```

### Cronología de un atacante específico
```logql
{container="levlab-gt-honeypot"}
  | json msg
  | line_format "{{.msg}}"
  | json
  | src="<ATTACKER_IP>"
  | line_format "{{.ts}} [{{.severity}}] {{.method}} {{.host}}{{.path}} ({{.category}})"
```

---

## Traefik — todo el tráfico

### Request rate por host
```logql
sum by (host) (rate({container="levlab-traefik"} | logfmt [1m]))
```

### 4xx ratio (recon signal)
```logql
sum by (host) (rate({container="levlab-traefik"} | logfmt | status >= 400 | status < 500 [5m]))
/
sum by (host) (rate({container="levlab-traefik"} | logfmt [5m]))
```

### Top user-agents
```logql
topk(20, sum by (user_agent) (count_over_time({container="levlab-traefik"} | logfmt [1h])))
```

### 401 spike (auth bruteforce)
```logql
sum by (remote_addr) (rate({container="levlab-traefik"} | logfmt | status="401" [1m])) > 10
```

### Path enumeration patterns (404 burst from same IP)
```logql
topk(20, sum by (remote_addr) (rate({container="levlab-traefik"} | logfmt | status="404" [5m])))
```

---

## App-level — auth events + vuln exploitation

### Logins en mobile BFF
```logql
{container="levlab-gt-mobile"} |~ "POST /v1/auth/login"
```

### Lockout triggers
```logql
{container="levlab-gt-mobile"} |~ "429|Too Many|locked"
```

### Tool RCE attempts on DVAIA (post-auth)
```logql
{container="levlab-gt-dvaia"}
  |~ "tool_call|exec_shell|read_file|write_file"
```

### Multi-tenant cross access (BOLA exploitation)
```logql
{container="levlab-gt-tenant"}
  |~ "tenant_id"
  | line_format "{{.message}}"
```

### LLM injection attempts (PromptMe)
```logql
{container="levlab-gt-promptme"}
  |~ "system_override|ignore"
```

---

## OS layer — Falco / fail2ban / AIDE

### Falco alerts (host-mode via journald)
```logql
{job="systemd-journal", unit="falco-modern-bpf.service"}
  |~ "Critical|Warning|Notice"
```

### Specific Falco rules triggered
```logql
{job="systemd-journal", unit="falco-modern-bpf.service"}
  |~ "Reverse Shell|Tmp Script Execution|Sensitive File Read|Container Escape"
```

### fail2ban bans
```logql
{job="systemd-journal", unit="fail2ban.service"}
  |~ "Ban "
```

### AIDE file integrity changes
```logql
{job="systemd-journal"}
  |~ "aide"
  |~ "added|changed|removed"
```

### SSH auth failures
```logql
{job="systemd-journal", unit="ssh.service"}
  |~ "Failed password|Invalid user"
```

---

## Cloudflare WAF — vía Logpush (requiere CF Pro $25/mo)

Free workaround: cron `curl https://api.cloudflare.com/client/v4/zones/$ZONE/security/events` → ship a Loki.

```bash
# Ejemplo cron host levlab cada 5min
*/5 * * * * curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/security/events?since=$(date -d '5 min ago' --utc +%FT%TZ)" \
  | jq -c '.result[]' \
  | logger -t cf-waf
```

Then Loki:
```logql
{job="systemd-journal"} |~ "cf-waf"
```

---

## Correlación cross-source — full attacker session

### Session timeline (combina honeypot + traefik + falco)
```logql
{container=~"levlab-gt-honeypot|levlab-traefik"} |~ "<ATTACKER_IP>"
```

### Honeytoken usage detection (post-auth)
Si Gonxa exfila datos plantados (ej. tokens en respuestas /v1/users/3 admin):
```logql
{container=~"levlab-gt-.*"}
  |~ "alice@melispy|bob@melispy|admin@melispy|99999.0"
```

(Nota: estos datos son los `USERS` simulados en mobile BFF — su aparición en headers/body de OTROS containers indica lateral movement.)

---

## Métricas para postmortem

### Total attacker requests in window
```logql
sum(count_over_time({container=~"levlab-traefik|levlab-gt-.*"} | logfmt [24h]))
```

### 401 / 403 / 200 ratio post-auth
```logql
sum by (status) (rate({container="levlab-traefik"} | logfmt | host=~"agent|chat|billing|mobile.melispy.com" [24h]))
```

### Time-to-first-honeypot-hit
```logql
{container="levlab-gt-honeypot"} |~ "category" | line_format "{{.ts}}" | first_over_time
```

### Total volumen tracking
```logql
sum(rate({container="levlab-gt-honeypot"} [24h])) * 3600 * 24
```

---

## Webhooks alert (gratis)

Loki Ruler con alerts → webhook Discord/Slack:

```yaml
# /opt/levlab/deploy/observability/loki-rules.yaml
groups:
  - name: levlab-alerts
    rules:
      - alert: HoneypotCriticalHit
        expr: |
          sum(rate({container="levlab-gt-honeypot"} | json msg | line_format "{{.msg}}" | json | severity="critical" [1m])) > 0
        for: 10s
        annotations:
          summary: "Critical honeypot hit"
      - alert: AuthBruteforceSpike
        expr: |
          sum by (remote_addr) (rate({container="levlab-traefik"} | logfmt | status="401" [1m])) > 30
        for: 1m
        annotations:
          summary: "Auth bruteforce >30/min from IP"
      - alert: FalcoCriticalAlert
        expr: |
          sum(rate({job="systemd-journal", unit="falco-modern-bpf.service"} |~ "Critical" [1m])) > 0
        annotations:
          summary: "Falco critical event"
```

---

## Quick triage script (para correr en VPS durante engagement)

```bash
#!/usr/bin/env bash
# /opt/levlab/scripts/triage.sh
# Cuick attacker overview last 1h

source /opt/levlab/.env.lab

echo "=== Top attacker IPs (honeypot) ==="
docker logs --since 1h levlab-gt-honeypot 2>&1 \
  | grep WARNING | grep -oE '"src": "[^"]*"' | sort | uniq -c | sort -rn | head -10

echo
echo "=== Honeypot categories triggered ==="
docker logs --since 1h levlab-gt-honeypot 2>&1 \
  | grep WARNING | grep -oE '"category": "[^"]*"' | sort | uniq -c | sort -rn

echo
echo "=== Falco alerts (host) ==="
journalctl --since "1 hour ago" -u falco-modern-bpf.service --no-pager \
  | grep -E "Notice|Warning|Critical|Error" | tail -10

echo
echo "=== fail2ban bans ==="
fail2ban-client status sshd | grep -A1 "Banned IP"

echo
echo "=== Top 401 sources ==="
docker logs --since 1h levlab-traefik 2>&1 \
  | grep -E ' 401 | 403 ' | awk '{print $1}' | sort | uniq -c | sort -rn | head -10
```
