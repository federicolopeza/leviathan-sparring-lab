# Leviathan Sparring Lab — Deploy Plan v2 (lean + hardened)

**Version:** 2026-04-25 · **Supersedes:** v1 (2026-04-23) — 28-stack ephemeral benchmark
**Engagement:** `LEV-MELISPY-GONXA-001` (blackbox vs Gonxa) + futuras corridas Leviathan internas
**Target:** `melispy.com` + `*.melispy.com` (zona Cloudflare activa, ya provisionada)

---

## TL;DR

Lab pentest **persistente y leveable** sobre Vultr Santiago, 6 containers core + GT rotator on-demand, hardening defensivo épico. Pensado para que **Gonxa pentest blackbox** y para corridas Leviathan internas. Cambia de "benchmark masivo 24h destroy-after" a "lab realista persistente con GT rotativo". Defensa-en-profundidad: cero IP pública entrante (Cloudflare Tunnel), WAF en modo activo (no log), CrowdSec + Fail2ban tuned, anti-recon, honeypots opcionales. Costo objetivo **$5-25/mo** según uso (ephemeral vs 24/7).

---

## Cambios vs v1

| Eje | v1 (deprecated) | v2 (este plan) |
|---|---|---|
| Goal | Benchmark Leviathan vs 28 stacks en 24h | Lab persistente + benchmark on-demand + sparring Gonxa |
| VPS | `vhp-8c-16gb-amd` $103/mo (480GB disk) | `vhp-2c-4gb-amd` $24/mo (100GB) — **-77%** |
| Region | New Jersey (`ewr`) | Santiago (`scl`) — latencia AR ↔ CL ~30ms |
| Containers en runtime | 28 targets + 10 obs + infra ≈ 40 | **6 core** + 1-2 GT activos via rotator |
| Lifecycle | Destroy-after 24h obligatorio | Snapshot+destroy on-demand (`lab-up`/`lab-down`) o 24/7 según preferencia |
| Observability | Wazuh+Suricata+Falco+Tetragon+Arkime+Loki+Grafana+ModSec | Loki+Promtail core, Falco opcional |
| GT activos | 131 entries en 28 stacks simultáneos | Catálogo 131 en repo, 1-2 stacks activos via `gt-rotate.sh` |
| WAF mode | Log only (Gonxa pasaba todo) | **Active block + custom rules** + JA3/JA4 anti-bot |
| Defensive posture | Bueno | **Épico** — cero IP pública, anti-recon CT pruning, honeypots opt-in |
| Costo target | <$5/24h ($150/mo si 24/7) | $5/mo ephemeral ó $25/mo 24/7 |

v1 docs siguen vivas pero con scope ajustado — sección [Re-scope docs](#re-scope-docs) lista qué tocar.

---

## Filosofía v2

1. **Defense-first**: lab simula target real. Gonxa (y Leviathan) atacan defensa real, no cartón
2. **Lean**: 6 containers > 40. Menos ataque-surface, menos mantenimiento, mismo aprendizaje
3. **Catalog vs runtime**: 131 GT siguen en repo, pero solo 1-2 activos. `gt-rotate.sh` los swappea
4. **Ephemeral real**: Vultr cobra apagado. Solo destroy corta cobro → lifecycle scripts
5. **Reproducible from-scratch**: nada de "snapshot bloated 480GB". Bootstrap idempotente desde Debian 12 fresh

---

## VPS spec final

| Setting | Valor |
|---|---|
| Provider | Vultr |
| Plan | `vhp-2c-4gb-amd` ($24/mo, $0.033/h) |
| Region | Santiago, CL (`scl`) |
| OS | Debian 12 x64 (bookworm) minimal |
| Disk | 100 GB NVMe |
| SSH key | `autop2p-migration` (existente Vultr) |
| Hostname | `levlab` |
| Backups Vultr | Disabled (snapshot manual + restic flow) |
| Firewall Group | `levlab-strict` (transitorio bootstrap, luego solo WG) |
| Connectivity | Public IPv4 inicial → cierre tras WG handshake |

---

## Stack final (6 containers core)

| # | Service | Image (pinned por digest) | Network | Rol |
|---|---|---|---|---|
| 1 | `cloudflared` | `cloudflare/cloudflared:2025.x` | `mgmt_net` | Tunnel — sustituye IP pública entrante |
| 2 | `traefik` | `traefik:v3.1` | `mgmt_net` + `target_net` | TLS interno + routing + middleware (rate limit, IP allowlist, basic-auth dashboards) |
| 3 | `kali` | `kalilinux/kali-rolling` | `attacker_net` | Toolkit attacker (uso interno Leviathan/manual) |
| 4 | `metasploit` | `metasploitframework/metasploit-framework` | `attacker_net` | Exploitation framework |
| 5 | `gt-active` | rotativo (catálogo `targets/`) | `target_net` (internal=true) | Target del momento |
| 6 | `loki` | `grafana/loki:3.x` | `mgmt_net` | Logs (Promtail sidecar, Grafana on-demand via tunnel) |

**Burp**: corre en laptop del operador, NO en VPS. Tunnel hacia `attacker_net` via WireGuard. Ahorra ~600MB RAM.

**GT rotator**: `gt-active` es slot único. Catálogo 37 stacks en `targets/` se montan via `gt-rotate.sh <stack-name>` que hace `compose down gt-active && compose up gt-active` con build context apropiado.

**Opcionales (opt-in via profile compose):**
- `falco` — runtime detection (≈+200MB RAM)
- `crowdsec` — community blocklist + bouncer
- `honeypot-cowrie` — SSH honeypot en port 2222 → alerts a Loki
- `grafana` — solo cuando consultás dashboards

---

## Networking

```
[Internet]
    │ NO IP pública entrante (UFW default-deny + Cloudflare Tunnel)
    │
    ▼
[Cloudflare]
    ├─ DNS melispy.com (zona ya activa)
    ├─ WAF Managed Rules + OWASP CRS PL2 + custom rules (active block)
    ├─ Bot Fight Mode + JA3/JA4 fingerprint
    ├─ Rate Limiting Rules (50 rps por IP, escalado WARFARE 150)
    └─ Tunnel `levlab-tunnel` → cloudflared container
    │
    ▼
[VPS Santiago — 2c/4GB]
    │ UFW: solo egress + WG inbound 51820/udp desde `179.24.190.234/32`
    │
    ├── docker net: mgmt_net      (cloudflared, traefik, loki, grafana opt-in)
    ├── docker net: attacker_net  (kali, metasploit) ─── WG peer access
    └── docker net: target_net    (gt-active) ── internal:true, sin egress salvo allowlist DNS
    │
    ▲
[WireGuard wg0 — peer único]
    │ UDP 51820 desde 179.24.190.234/32
    └── operador laptop (admin SSH + Burp upstream proxy)
```

**Reglas net duras:**
- `target_net` con `internal: true` → containers GT no pueden hacer egress salvo via Traefik proxy whitelistado (DNS + apt mirror durante build, después blocked)
- `attacker_net` ↔ `target_net` permitido (es el punto del lab)
- `mgmt_net` ↔ `target_net` permitido solo Traefik
- WG peer único: tu laptop. NO multi-peer salvo nuevo handshake explícito

---

## Hardening checklist (épico, post-bootstrap)

### OS layer
- [ ] User no-root + sudo NOPASSWD (solo durante bootstrap, después password-required)
- [ ] SSH `PermitRootLogin no`, `PasswordAuthentication no`, `AllowUsers <user>`, `MaxAuthTries 3`, `ClientAliveInterval 300`, custom port `49222`
- [ ] SSH **solo accesible via WG `10.8.0.0/24`** post-handshake
- [ ] `unattended-upgrades` security only, `Unattended-Upgrade::Automatic-Reboot "false"` (controlled)
- [ ] `auditd` con reglas CIS Debian 12 baseline
- [ ] `aide` baseline + cron diario, integridad enviada a Loki
- [ ] `fail2ban` jails: SSH (post-WG), traefik-auth, traefik-ratelimit
- [ ] `lynis audit system` baseline → score ≥ 80, gates en CI
- [ ] `rkhunter` weekly scan
- [ ] Banner SSH "warning authorized access only" (legal)
- [ ] `chrony` NTP (timestamps correctos para forensics)

### Kernel sysctl (`/etc/sysctl.d/99-levlab.conf`)
- [ ] `kernel.kptr_restrict=2`
- [ ] `kernel.dmesg_restrict=1`
- [ ] `kernel.yama.ptrace_scope=2`
- [ ] `kernel.unprivileged_bpf_disabled=1`
- [ ] `net.ipv4.conf.all.rp_filter=1`
- [ ] `net.ipv4.conf.all.accept_redirects=0`
- [ ] `net.ipv4.conf.all.send_redirects=0`
- [ ] `net.ipv4.conf.all.accept_source_route=0`
- [ ] `net.ipv4.tcp_syncookies=1`
- [ ] `net.ipv4.icmp_echo_ignore_broadcasts=1`
- [ ] `net.ipv6.conf.all.disable_ipv6=1` (si no se usa)
- [ ] `fs.suid_dumpable=0`

### Network
- [ ] UFW default-deny inbound, allowlist outbound restrictivo (53, 80, 443, NTP 123, WG 51820)
- [ ] WireGuard `wg0` con peer único, `PersistentKeepalive=25`, claves ED25519
- [ ] Cloudflare Tunnel egress only — NO listen externo
- [ ] Cloudflare WAF: Managed Rules ON, OWASP CRS PL2 active block, Bot Fight Mode ON
- [ ] Cloudflare custom rules:
  - Block conocido scanner UA (sqlmap/nuclei/nikto/masscan) salvo override header
  - Rate limit 50 rps por IP `*.melispy.com`
  - Challenge JS para non-AS-Argentina/Chile/UY hosts (excepto Gonxa IP whitelisted)
- [ ] Cloudflare Access (zero-trust) en panels admin (`grafana.melispy.com`, `traefik.melispy.com`) — email + 2FA
- [ ] DNS: solo records necesarios públicos. NO wildcards `*.melispy.com` apuntando a algo. Subdominios `gt-*` solo via Tunnel ingress rules

### Docker
- [ ] `userns-remap` enabled (`/etc/docker/daemon.json`)
- [ ] Daemon: `live-restore: true`, `no-new-privileges: true`, `userland-proxy: false`
- [ ] Por container:
  - `cap_drop: [ALL]` + `cap_add` mínimo necesario
  - `read_only: true` + `tmpfs` para `/tmp`, `/run`
  - `security_opt: [no-new-privileges:true, apparmor=docker-default, seccomp=/etc/docker/seccomp/levlab-default.json]`
  - `pids_limit: 200`, `mem_limit: 512m` default, `cpus: 0.5` default
  - `user: 1000:1000` (no root in container)
- [ ] Imágenes pinned por digest `image@sha256:...`, NO `latest`
- [ ] `trivy` scan local pre-pull, score ≥ HIGH bloquea
- [ ] Networks `internal: true` para target_net
- [ ] Secrets via Docker secrets file-based, NO env plano
- [ ] `/var/lib/docker` en partición separada con `nodev,nosuid,noexec` donde aplique

### Cloudflare específico (defensa anti-Gonxa)
- [ ] **Anti-recon**: certificate transparency pruning — usar Cloudflare cert SAN único, no listar todos subdominios
- [ ] **Anti-enum**: NO zone transfer público, NO wildcard DNS, NO recursive resolver
- [ ] **WAF custom**: bloquear payloads SQLi/XSS/SSRF default + log
- [ ] **Anomaly Detection** (Pro plan only) — si tenés
- [ ] **Tunnel ingress rules** explícitas por hostname → no fallthrough a default backend
- [ ] **Hostname header validation** — Traefik rechaza requests con Host no matched

### Runtime monitoring (opt-in stack)
- [ ] `falco` host-mode con custom rules para Gonxa expected TTPs (priv-esc, /tmp persistence, reverse shell, container breakout)
- [ ] `crowdsec` con CTI feed + bouncer en Traefik
- [ ] `osquery` para incident response post-engagement
- [ ] Logs centralizados Loki: SSH auth, sudo, docker events, WAF blocks, fail2ban bans, falco alerts

### Backup / lifecycle
- [ ] Snapshot Vultr semanal automatizado vía Vultr API + cron en VPS o GitHub Actions
- [ ] Volumes críticos (`/var/lib/loki`, `/etc/wireguard`, `engagements/`) → restic a Backblaze B2 cifrado AES-256
- [ ] Retención: 4 semanales + 3 mensuales
- [ ] Restore drill mensual

---

## Defensa específica anti-Gonxa (elevación pentest)

Gonxa hace blackbox sobre `melispy.com`. v1 era fácil — WAF en log, subdominios listados en CT, GT siempre live. v2 sube el listón:

| Lo que sufre Gonxa | Mecanismo defensa v2 |
|---|---|
| Recon subdomain | CT pruning + DNS dinámico via Tunnel ingress (no records públicos), tiene que adivinar |
| Wildcard DNS brute | NO wildcard `*.melispy.com`. Cada subdominio explícito en Tunnel rules. Brute = 99% NXDOMAIN |
| Banner grab | Cloudflare proxy → no ve VPS real, ve CF edge. Headers custom strip server/version |
| Default scanner UAs | WAF custom rule bloquea `sqlmap/nuclei/nikto/dirb/gobuster` UA salvo header bypass |
| Rate scan | CF Rate Limiting 50 rps + per-IP, escala a challenge |
| Auth bruteforce | CF Login Protection + fail2ban Traefik + lockout post 5 intentos |
| /robots.txt + /sitemap.xml leaks | Servidos vacíos o decoy con honeypot paths |
| Predictable paths (/admin /wp-admin) | Honeypots con detection alert (Falco/Loki) |
| GT siempre live | Solo 1-2 activos. Gonxa tiene que descubrir cuáles, no escanear lista fija |
| Source code review | Repos seeded NO públicos en CI/CD ahora, Gonxa los explota desde dentro si llega |
| Persistence post-exploit | AIDE detect changes → alert → opcional auto-rollback |

**Trade-off explícito**: lab más cerrado = menos findings "fáciles". Pero los que encuentra son **reales** y representativos de target hardened. Métricas más significativas.

---

## Costos v2

| Modo | Componente | Costo/mo |
|---|---|---|
| **Ephemeral (4-6h/día)** | VPS prorrateado | ~$4 |
|  | Snapshot storage 10GB | $0.50 |
|  | B2 backup ~5GB | $0.03 |
|  | Cloudflare Free | $0 |
|  | **Total** | **~$5/mo** |
| **24/7 persistente** | VPS | $24 |
|  | Snapshot storage | $0.50 |
|  | B2 backup | $0.03 |
|  | **Total** | **~$25/mo** |

Para engagement Gonxa 24h: $0.79 (24h × $0.033/h).
Para corrida Leviathan 24h: $0.79 + tokens Opus.

---

## Estructura repo (post-reorg)

```
leviathan-sparring-lab/
├── vultr-deploy-plan.md          # ← ESTE doc, source of truth
├── README.md                     # quickstart actualizado
├── HANDOFF.md                    # session state, contexto entre runs
├── CLAUDE.md                     # instrucciones específicas repo (a crear)
│
├── docs/                         # rescope per [Re-scope docs] sección
│   ├── 00-overview.md            # v2 overview (re-scope)
│   ├── 01-architecture.md        # 6-container topo (re-scope)
│   ├── 02-infrastructure.md      # Terraform CF-only + Ansible lean (re-scope)
│   ├── 03-hardening.md           # checklist épico (mover de plan v2 acá)
│   ├── 04-targets-catalog.md     # rename de zoo-targets (re-scope catalog vs runtime)
│   ├── 05-ground-truth.md        # entries siguen, distribución por GT (re-scope)
│   ├── 06-observability.md       # lean: Loki + opcionales (re-scope)
│   ├── 07-roe.md                 # lab.yaml vigente per engagement
│   ├── 08-runbook.md             # 24h Leviathan + ops cotidiano (re-scope)
│   ├── 09-metrics-scoring.md     # vigente con métricas defensivas extra
│   ├── 10-postmortem.md          # template vigente
│   ├── 11-operations.md          # scripts nuevos (lab-up/down/rotate)
│   ├── 12-checklists.md          # pre/post v2
│   ├── 13-credentials-guide.md   # vigente
│   └── 14-defense-playbook.md    # NEW — playbook anti-recon, anti-attack, IR
│
├── .env.lab                      # ya existe (gitignored)
├── .env.lab.example              # update con CF_TUNNEL_INGRESS, defensive flags
│
├── terraform/                    # CF-only ya configurado, ajustes menores
│   ├── main.tf                   # records + ruleset + tunnel
│   ├── providers.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
│
├── ansible/                      # lean: solo lo que se usa post-bootstrap
│   ├── ansible.cfg
│   ├── site.yml                  # playbook único idempotente
│   ├── inventory.tmpl
│   └── roles/
│       ├── os-hardening/         # sysctl, ssh, ufw, fail2ban, auditd, aide
│       ├── docker/               # daemon.json + userns + seccomp + apparmor
│       ├── wireguard/            # wg0 + peer
│       ├── cloudflared/          # tunnel cred + service
│       ├── monitoring/           # loki + promtail + falco opt-in
│       └── lab-stack/            # docker-compose deploy
│
├── docker-compose.yml            # → renombrar a docker-compose.legacy.yml (28 stacks)
├── docker-compose.lean.yml       # NEW — 6 containers core + GT slot
├── docker-compose.opts.yml       # NEW — falco/crowdsec/honeypot opt-in profiles
│
├── targets/                      # 37 catálogo, todos siguen
│   ├── catalog.yml               # NEW — metadata por GT (CVE, severity, network reqs)
│   └── <stack-dirs>/             # Dockerfiles + seed data
│
├── ground_truth/
│   └── ground_truth.yml          # 131 entries vigente
│
├── scripts/                      # cleanup
│   ├── lab-up.sh                 # NEW — deploy VPS + bootstrap (Vultr API + Ansible)
│   ├── lab-down.sh               # NEW — snapshot + destroy VPS
│   ├── gt-rotate.sh              # NEW — swap GT activo
│   ├── harden.sh                 # NEW — idempotent OS hardening (one-shot)
│   ├── lynis-baseline.sh         # NEW — score gate
│   ├── trivy-scan.sh             # NEW — image scan pre-deploy
│   ├── waf-test.sh               # NEW — verify CF rules functional
│   ├── bootstrap.sh              # legacy → revisar/refactor
│   ├── teardown.sh               # legacy → revisar/refactor
│   ├── kill.sh                   # vigente
│   ├── smoke.sh                  # update para 6 containers
│   ├── export-artifacts.sh       # vigente
│   ├── generate-wg-keys.sh       # vigente
│   ├── build-scoreboard.py       # vigente
│   ├── reconcile.py              # vigente
│   ├── validate-ground-truth.py  # vigente
│   └── vultr-preflight.sh        # update con SCL region
│
├── lab.yaml                      # ROE base Leviathan
├── engagements/
│   └── LEV-MELISPY-GONXA-001/    # engagement Gonxa (vigente)
│       └── ...
│
├── GONXA-BRIEFING.md             # vigente, update con v2 changes
└── postmortem-template.md        # vigente
```

---

## Re-scope docs

Docs `00-13` siguen siendo válidas pero algunas necesitan re-scope. Tabla:

| Doc | Status | Acción |
|---|---|---|
| 00-overview | re-scope | reescribir analogía con 6 containers + lifecycle ephemeral |
| 01-architecture | re-scope | reemplazar topo 12 docker bridges por 3 networks lean |
| 02-infrastructure | re-scope | Terraform CF-only ya implementado, simplificar Ansible |
| 03-hardening | EXPAND | mover checklist épico de este plan acá, agregar runtime monitoring |
| 04-zoo-targets | rename + re-scope | → `04-targets-catalog.md`, distinguir catálogo vs activo |
| 05-ground-truth | minor | mantener 131 entries, agregar `active_in_lab` flag |
| 06-observability | re-scope | recortar a Loki+Promtail core + Falco opt-in |
| 07-roe | minor | seguir vigente, lab.yaml por engagement |
| 08-runbook | re-scope | agregar runbook ops cotidiano (no solo 24h benchmark) |
| 09-metrics-scoring | EXPAND | métricas defensivas (WAF block rate, fail2ban hits, AIDE delta) |
| 10-postmortem | minor | template vigente |
| 11-operations | re-scope | scripts nuevos, lifecycle commands |
| 12-checklists | re-scope | v2 pre/post deploy |
| 13-credentials-guide | minor | actualizar con WG keys + B2 |
| **14-defense-playbook** | NEW | crear |

Re-scope se hace incremental. **No bloquea bootstrap v2**.

---

## Ejecución — orden cronológico

### Fase 0 — Pre-deploy (vos, ahora)
- [x] Decision: Santiago + Debian 12 + 2c/4GB
- [ ] Crear Firewall Group `levlab-strict` Vultr (SSH 22 desde `179.24.190.234/32` solamente)
- [ ] Deploy fresh VPS Vultr Santiago `levlab` (sin snapshot)
- [ ] Pasarme IP pública resultante
- [ ] (opcional) Decidir delete snapshot 480GB vieja + VPS NJ vieja (cuesta $24/mo storage suelta)

### Fase 1 — Repo reorg (yo, antes que vos termines deploy)
- [ ] Escribir `vultr-deploy-plan.md` v2 ✅ (este doc)
- [ ] Escribir `HANDOFF.md` con session state
- [ ] Update `README.md` con quickstart v2
- [ ] Crear stub `docs/14-defense-playbook.md`
- [ ] Renombrar `docker-compose.yml` → `docker-compose.legacy.yml`
- [ ] Crear `targets/catalog.yml` con metadata 37 stacks

### Fase 2 — Stack lean (yo)
- [ ] Escribir `docker-compose.lean.yml` (6 containers core)
- [ ] Escribir `docker-compose.opts.yml` (falco/crowdsec/honeypot profiles)
- [ ] Escribir `scripts/harden.sh` (idempotent OS hardening)
- [ ] Escribir `scripts/gt-rotate.sh`
- [ ] Escribir `scripts/lab-up.sh` y `lab-down.sh`
- [ ] Escribir `scripts/waf-test.sh`
- [ ] Escribir `scripts/lynis-baseline.sh`
- [ ] Update `.env.lab.example` con vars defensivas

### Fase 3 — Bootstrap real (vos + yo, post deploy VPS)
- [ ] `.env.lab` actualizado con `VULTR_VPS_IP=<nuevo>`
- [ ] SSH initial (vía firewall group temporal)
- [ ] Run `bash scripts/harden.sh` (idempotent, completable en pasos)
- [ ] Generate WG keys + handshake desde laptop
- [ ] Cerrar Firewall Group SSH público (todo via WG ahora)
- [ ] Run `docker compose -f docker-compose.lean.yml up -d`
- [ ] `lynis audit system` → score ≥ 80
- [ ] `nmap` desde fuera → 0 puertos abiertos públicos (todo via tunnel/WG)
- [ ] Cloudflare Tunnel ingress rules → containers
- [ ] Smoke test: `https://traefik-dashboard.melispy.com` (tras CF Access auth)

### Fase 4 — Hardening defensivo (yo)
- [ ] Cloudflare WAF custom rules vía Terraform (anti-bot, anti-scanner)
- [ ] CrowdSec install + bouncer
- [ ] Falco rules customizadas anti-Gonxa TTPs
- [ ] Honeypots opt-in (cowrie SSH, decoy `/admin`)
- [ ] AIDE baseline + cron
- [ ] Test pasivo: `nuclei`/`nikto` desde IP no whitelisted → bloqueado

### Fase 5 — Re-scope docs (incremental, post-deploy)
Por orden de impacto:
1. `docs/14-defense-playbook.md` (NEW) — playbook IR + anti-recon
2. `docs/03-hardening.md` — checklist épico
3. `docs/01-architecture.md` — topo lean
4. `docs/04-targets-catalog.md` — rename + catalog vs runtime
5. `docs/06-observability.md` — recortar
6. `docs/00-overview.md` — analogía v2
7. Resto on-demand

### Fase 6 — Cleanup
- [ ] Destroy VPS NJ viejo `levlab-ephemeral` (e754ad58-...)
- [ ] Destroy snapshot 480GB (97fcac9e-...) tras confirmar nada útil dentro
- [ ] Rotar API key Vultr (la pegada en chat está quemada)
- [ ] Update CF Access list con tu IP whitelisted
- [ ] Commit todo + push

### Fase 7 — Engagement Gonxa
- [ ] `GONXA-BRIEFING.md` actualizado con cambios v2
- [ ] `engagements/LEV-MELISPY-GONXA-002/` (nuevo run sobre v2)
- [ ] Coordinar window 24h
- [ ] Comparar findings vs Leviathan paralelo

---

## Decisiones pendientes

1. **Burp**: laptop only ✅ (default v2). Si querés headless en VPS también, decime
2. **GT primero activo**: ¿`dvwa`, `juice-shop`, `crapi`, `vampi`, otro? Para empezar elegí 1
3. **Falco día 0 o opt-in**: voto opt-in (RAM 4GB justa). Lo activamos cuando Gonxa empiece a atacar
4. **Honeypot cowrie**: opt-in (otros +50MB). Útil para detectar Gonxa scanning SSH
5. **Snapshot 480GB vieja**: rescatar algo o delete directo (cuesta $24/mo storage)
6. **VPS NJ viejo**: destroy ya o esperar?
7. **Modo runtime**: ephemeral lifecycle vs 24/7. Voto **24/7** para pentest Gonxa (necesita atacarlo cuando quiera), después ephemeral para benchmarks Leviathan
8. **Cloudflare plan**: Free está bien o Pro ($25/mo) para Anomaly Detection + más Page Rules? Voto Free, agregás Pro solo si Gonxa rompe demasiado

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| 4GB RAM corto si activan todos opts | Profiles compose, monitoring `mem_limit` por container |
| Cloudflare Tunnel cae → lab inalcanzable | `cloudflared` `restart: always` + alert Loki si down >5min |
| WG peer único pierde conexión (IP residencial dinámica) | Backup: Tailscale opt-in como segundo path admin |
| Gonxa logra container breakout | userns-remap + apparmor + seccomp + falco alert + auto-snapshot pre-engagement |
| Bootstrap script roto a mitad | Idempotente con flags `--phase=os|docker|monitoring|stack` |
| Cloudflare API token leak | Token con scope mínimo (Zone DNS edit + WAF + Tunnel only), rotación trimestral |

---

## Comparación métrica esperada — Gonxa contra v1 vs v2

| Métrica | v1 (28 stacks live, WAF log) | v2 (1-2 GT live, WAF active + hardening) |
|---|---|---|
| Subdominios descubiertos en 1h | ~30+ via wildcard | ~5-10, brute heavy |
| WAF blocks observados | 0 (log only) | 100s (active) |
| Critical findings 24h | 15-25 | 5-10 (cada uno **real**) |
| Time to first critical | 1-2h | 4-8h |
| Token spend Leviathan | $20-40 | $30-60 (más recon needed) |
| Detecciones blue side | low (pasivo) | rich (Falco/CrowdSec/AIDE/Loki) |

v2 mide ataque **realista**. v1 medía cobertura amplia pero unrealistic.

---

## Próximo paso inmediato

Vos: terminás deploy Vultr Santiago y me pasás IP.
Yo (paralelo): empiezo Fase 1 (HANDOFF + README + reorg files).

Cuando converjan los dos paths → Fase 3 bootstrap real.
