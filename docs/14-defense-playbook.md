# 14 — Defense Playbook (anti-recon + anti-attack + IR)

**Status:** stub v0 — expansión incremental post-bootstrap.
**Owner:** blue side (operador).
**Sparring partners:** Gonxa (blackbox), Leviathan interno.

---

## Propósito

Playbook defensivo del lab. Tres capas:
1. **Anti-recon** — qué hacer para que enumerar `melispy.com` sea costoso
2. **Anti-attack** — qué hacer para que explotar lo enumerado sea costoso
3. **IR (incident response)** — qué hacer cuando atacante logra algo

Orientado a **elevar el costo del atacante**, no a hacer el lab invulnerable. Lab tiene targets vulnerables intencionalmente — la defensa rodea, no reemplaza.

---

## Anti-recon

### DNS hygiene
- Zona `melispy.com` con records explícitos solamente. NO `*.melispy.com` apuntando a algo
- TTL bajo (300) en records dinámicos para revocación rápida
- DNSSEC habilitado en zona Cloudflare
- NO zone transfer público (`AXFR` rechazado)
- NO `_dmarc`/`_spf` filtrados leakeando infraestructura interna

### Certificate Transparency
- Cloudflare Universal SSL → cert único multi-SAN cubre todos subdominios sin listarlos en CT
- Custom certs solo si necesario; nunca crear cert per-subdomain (cada uno = entry CT pública)
- Revisar `crt.sh?q=melispy.com` periódicamente — si aparecen subdominios no esperados, investigar

### Tunnel ingress rules
- Cloudflare Tunnel `levlab-tunnel` config con ingress rules explícitas:
  ```yaml
  ingress:
    - hostname: gt.melispy.com
      service: http://traefik:80
    - hostname: traefik.melispy.com
      service: http://traefik:8080
    - service: http_status:404
  ```
- Catch-all `404` impide que requests con Host arbitrario pasen
- Nunca usar wildcard ingress

### Banner / fingerprint scrub
- Traefik response headers: strip `Server`, `X-Powered-By`, etc
- Custom `Server: nginx` decoy si querés despistar
- HTTP error pages custom genéricas — no leak stack version

### WAF custom rules anti-recon
- Bloquear UAs scanner default (`sqlmap`, `nuclei`, `nikto`, `dirb`, `gobuster`, `wfuzz`, `ffuf`, `feroxbuster`) → return 403
  - Override header `X-Lab-Bypass: <secret>` para testing autorizado interno
- Bloquear paths fingerprint comunes que no debas servir (`/.git/`, `/.env`, `/wp-admin/install.php`) — return 404 (no 403, evita confirmar existencia)
- Rate limit per-IP en endpoints de discovery (`/api/`, `/v1/`) más bajo que páginas normales

### Active deception
- Decoy `/robots.txt` con disallows fake
- Decoy `/sitemap.xml` minimal
- Honeypot subdominio `dev.melispy.com` o `staging.melispy.com` → cowrie + alert Loki

---

## Anti-attack

### Edge layer (Cloudflare)
- Managed Rules: ON, action `Block`
- OWASP Core Rule Set: PL2 minimum, action `Block`
- Bot Fight Mode: ON
- Browser Integrity Check: ON
- Challenge JS para non-AS-Argentina/Chile/Uruguay (lista dinámica)
- Rate Limiting Rules:
  - 50 rps por IP across `*.melispy.com` → action `Challenge`
  - 5 rpm por IP en endpoints auth → action `Block` 5min
- Geo-block país sospechoso (CN/RU/KP/etc) si no parte de scope engagement
- Cloudflare Access (zero-trust) en panels admin (`grafana.`, `traefik.`) — email + 2FA

### App layer (Traefik middleware)
- IP allowlist en panels admin (`179.24.190.234/32`)
- Basic auth en `/dashboard` Traefik con password rotada
- Rate limit middleware: 100 rps burst 50 por IP
- Compress + redirect HTTPS only
- Hostname header strict matching — Host no whitelisted → 421

### Container layer
- Per-container security_opt (ver `vultr-deploy-plan.md` hardening checklist)
- target_net `internal: true` — GT no puede salir a internet salvo via Traefik proxy whitelisted
- attacker_net ↔ target_net permitido (point del lab)
- Resource limits: `mem_limit`, `cpus`, `pids_limit` para evitar resource exhaustion

### Auth bruteforce
- Fail2ban Traefik jail con regex 401/403 spike
- Cloudflare Login Protection (Pro+) si disponible
- Lockout 5 intentos failed → 15min ban

### Lateral movement controls
- target_net subnets aisladas del resto VPS
- NO mounting `/var/run/docker.sock` en containers (escape vector)
- NO `--privileged`
- NO `--cap-add SYS_ADMIN/NET_ADMIN` salvo container especifico requerido

### Persistence detection
- AIDE FIM `/etc`, `/usr/bin`, `/usr/sbin`, `/var/spool/cron`, `/etc/systemd/system` baseline + cron horario
- Auditd reglas para `execve` en `/tmp`, `/dev/shm`, escritura a binarios sistema
- Falco reglas custom:
  - Reverse shell signatures (curl|bash, wget|sh, nc, socat)
  - `/tmp/*.sh` execute
  - `crontab -e` o write to `/etc/cron.d`
  - SSH key write to `~/.ssh/authorized_keys`
  - sudoers modification
  - `userns-remap` escape attempts

---

## IR (incident response)

### Pre-engagement (preparación)
- Snapshot Vultr pre-engagement (línea base limpia)
- AIDE baseline reset
- `docker ps -a > pre.txt`, `ss -tnlp > ports-pre.txt`, `iptables-save > fw-pre.txt`
- Hash-chain initial evidence directory

### Durante engagement (monitoreo activo)
- Tail Loki dashboard `pentest-overview` — eventos clave:
  - WAF blocks (CF logs via Logpush a Loki)
  - SSH auth failures (post-WG, debería ser ~0)
  - Falco alerts (cualquier severity ≥ Notice)
  - AIDE diff alerts
  - CrowdSec decisions
- Si Falco severity `Critical`: pausar engagement, snapshot, analizar
- Si container breakout detectado: kill container, restore desde snapshot, document path

### Post-engagement (forense + remediation)
- `bash scripts/export-artifacts.sh <engagement-id>` — bundle:
  - Loki logs window
  - Falco alerts
  - WAF logs CF
  - AIDE deltas
  - Container diffs (`docker diff <name>`)
  - File integrity hash-chain
- Map findings ↔ Gonxa report ↔ ground truth
- Chain rota → teardown aborta, dump state, investigate
- Update Falco rules con TTPs nuevas observadas
- Update WAF custom rules con bypasses descubiertos

### Escalation triggers
| Trigger | Acción |
|---|---|
| Container breakout (Falco crit) | Kill container, snapshot, restore baseline |
| VPS root compromise (sudo abuse) | Destroy VPS, rotate keys, redeploy from `lab-up.sh` |
| Cloudflare Tunnel cae >5min | Auto-restart cloudflared; si persiste, switch backup tunnel |
| WG peer pierde conexión | Detect via Tailscale fallback (si configurado) |
| Loki/storage 90% | Auto-archive `engagements/` antiguos a B2 |
| WAF block rate spike >1000/min | Trigger CF Under Attack Mode |

---

## Métricas defensivas (para [09-metrics-scoring](09-metrics-scoring.md) v2)

Agregar al scoreboard:

| Métrica | Definición | Fuente |
|---|---|---|
| WAF block rate | blocks/total requests | CF Analytics + Logpush |
| WAF false positive rate | blocks legítimos / total blocks | manual review post-eng |
| Fail2ban hits | bans triggered en window | fail2ban-client status |
| Falco alerts severity-weighted | sum(severity_weight × count) | Loki query |
| AIDE deltas | files modified post-baseline | aide --check output |
| Time to detect (TTD) | first attack request → first alert | Loki correlation |
| Time to respond (TTR) | first alert → mitigation deploy | manual log |
| Subdomain enumeration cost | requests sent / subdomains found | CF Analytics |
| Mean attacker request rate before challenge | avg rps until rate limit triggers | CF logs |

Comparar Gonxa v1 vs Gonxa v2:
- v1: defensa pasiva, métricas mide solo offense
- v2: defensa activa, mide trade-off offense vs defense

---

## Pendiente expandir (TODO)

- [ ] WAF custom rules YAML completas (Terraform `cloudflare_ruleset`)
- [ ] Falco rules YAML completas
- [ ] CrowdSec scenarios YAML
- [ ] AIDE config tuned
- [ ] Auditd rules CIS Debian 12
- [ ] Runbook IR step-by-step por escenario (breakout / persistence / exfil)
- [ ] Checklist pre-engagement / post-engagement
- [ ] Decoy / honeypot deployment guide
- [ ] Threat intel feeds integration (CrowdSec CTI, OTX, etc)

Expansión per Fase 4 del [plan v2](../vultr-deploy-plan.md#fase-4--hardening-defensivo-yo).
