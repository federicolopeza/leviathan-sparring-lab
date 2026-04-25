# Leviathan Sparring Lab — Estado actual

**Última actualización:** 2026-04-25 (post bootstrap v2 Santiago)
**One-liner:** Lab pentest persistente con stack 2026 (AI/LLM/SaaS/fintech) en `melispy.com` para que Gonxa attackee blackbox + Leviathan haga benchmarks.

---

## El goal en 1 párrafo

Tener un **target realista 2026** corriendo 24/7 sobre `melispy.com` con apps que parecen un SaaS real moderno (AI agent, fintech billing, mobile BFF, storefront). Gonxa hace pentest blackbox desde su laptop con Leviathan UI, descubre subdomains, explota vulnerabilidades 2026 (prompt injection, tool RCE, multi-tenant IDOR, weak JWT, OWASP top 10), todo mientras Cloudflare WAF + Traefik + Loki capturan métricas defensivas. Después comparamos lo que él encontró vs lo que Leviathan encuentra solo.

---

## Antes (v1, 2026-04-23) vs Ahora (v2, 2026-04-25)

| Aspecto | v1 (deprecada) | v2 (vivo) |
|---|---|---|
| **Goal** | Benchmark Leviathan vs 28 stacks en 24h destroy-after | Lab persistente + Gonxa engagement + Leviathan recurrente |
| **Stack apps** | 28 apps zoo (DVWA, Drupal, WordPress, Jenkins…) — **2014-2017 era** | 6 GTs **2026 era** (AI agent, LLM, SaaS multi-tenant, mobile BFF) |
| **VPS** | `vhp-8c-16gb-amd` $103/mo NJ | `vhp-2c-4gb-amd` $24/mo Santiago |
| **Disk** | 480 GB (snapshot bloated) | 100 GB fresh |
| **Lifecycle** | 24h ephemeral obligatorio (terraform destroy) | Persistente o ephemeral on-demand vía `lab-up`/`lab-down` |
| **Containers runtime** | ~40 (28 targets + 10 obs) | 11 (6 GTs + traefik + cloudflared + kali + metasploit + loki/promtail) |
| **Observability** | Wazuh+Suricata+Falco+Tetragon+Arkime+Loki+Grafana+ModSec | Loki+Promtail core, Falco/CrowdSec opt-in |
| **DNS** | Wildcard `*.melispy.com` | 18 records explícitos, sin wildcard (anti-recon) |
| **Tunnel ingress** | 23 rules apuntando a v1 containers | 15 rules → Traefik (que rutea por hostname) |
| **Hardening** | Bueno (AIDE, Fail2ban, AppArmor) | Épico (anti-recon CT pruning + custom rules + middleware + WAF) |
| **WAF mode** | Log only (Gonxa pasaba todo) | Active block + rate limit + bot detection (a configurar) |

---

## Quién es quién (componentes)

### Capa 1: Edge (Cloudflare) — defensa pública
| Pieza | Rol |
|---|---|
| **Cloudflare DNS** | Resuelve `melispy.com` + 17 subdomains a tunnel CNAME (proxy ON) |
| **Cloudflare WAF** | Filtra requests maliciosas antes que lleguen al VPS |
| **Cloudflare Tunnel** | Conexión saliente desde VPS (no IP pública entrante). 4 conexiones activas |
| **Cloudflare Bot Fight Mode** | Detecta bots default (a activar) |

### Capa 2: VPS (Vultr Santiago `64.176.15.72`) — sistema
| Pieza | Rol |
|---|---|
| **Debian 12** | OS minimal hardened (sysctl kernel, auditd, AIDE FIM, fail2ban) |
| **Docker 28.5.2** | Container runtime |
| **WireGuard wg0** | Admin tunnel (peer único, no started aún — pendiente client config) |
| **UFW + fail2ban** | Firewall + ban automático brute-force SSH (ya baneó 1 atacante hoy) |
| **lynis + AIDE + auditd** | Auditoría OS + integridad archivos + log syscalls sospechosos |

### Capa 3: Stack lab (Docker compose lean) — apps
| Container | Rol | URL |
|---|---|---|
| `cloudflared` | Tunnel saliente CF | (interno) |
| `traefik` | Reverse proxy + TLS interno + middleware (rate limit / security headers) | (interno) |
| `kali` | Toolkit attacker (uso operador interno) | (interno) |
| `metasploit` | Exploitation framework (uso operador interno) | (interno) |
| `loki` + `promtail` | Logs centralizados | (interno) |
| `gt-landing` | Decoy SaaS landing page | `melispy.com`, `www`, `lab`, `gt` |
| `gt-dvaia` | AI agent vulnerable (tool-calling RCE, prompt injection) | `agent`, `ai` |
| `gt-promptme` | LLM proxy (prompt injection, system override) | `chat`, `assistant` |
| `gt-tenant` | SaaS multi-tenant billing (IDOR, tenant escape) | `billing`, `saas` |
| `gt-mobile` | Mobile BFF (weak JWT alg=none, hardcoded keys, IDOR) | `mobile`, `app` |
| ~~gt-juice~~ | **REMOVED** — Juice Shop está en training data de Leviathan (`arsenal/benchmarks/runner.py` lo reconoce instant). Findings ahí = freebies, no miden capacidad real. Para benchmark genuino sólo apps custom 2026. | ~~shop~~ |

### Capa 4: Engagement (humanos + tooling)
| Quien | Rol |
|---|---|
| **Gonxa** (atacante humano) | Blackbox pentest. Recon → fingerprint → explotación → reporta findings |
| **Leviathan 8.2** (atacante autónomo) | Mismo target. Run paralelo desde laptop operador. UI dashboard `localhost:3456` |
| **Operador** (vos) | Configuración + observación + comparación post-engagement |
| **Loki/Falco** (defensa observadora) | Capturan TTPs blue-team |

---

## Para qué sirve cada cosa

| Si querés… | Usá… |
|---|---|
| Que Gonxa attackee blackbox | `https://melispy.com` (le pasás solo el apex) |
| Configurar el lab desde tu laptop | `make up` / `make rotate STACK=<name>` / `make audit` |
| Ver si el lab está vivo | `curl -sI https://melispy.com` (o cualquier subdomain) |
| Ver logs en tiempo real | `make logs` |
| Tear down (snapshot + destroy VPS) | `make down` |
| Cambiar GT activos | editar `docker-compose.lean.yml` o `gt-rotate.sh` |
| Agregar nuevo target | crear `targets/<name>/Dockerfile` + entry en `targets/catalog.yml` + service en compose |
| Run hardening idempotent | `make harden` |
| Lynis score audit | `make audit` |
| Re-correr Leviathan benchmark | abrir `http://127.0.0.1:3456` (laptop), `/pentest melispy.com --roe lab.yaml --mythos warfare` |

---

## Costos actuales

| Item | $/mo |
|---|---|
| VPS Santiago `vhp-2c-4gb-amd` 24/7 | $24 |
| Snapshot 480GB vieja (a destruir) | $24 ⚠️ |
| VPS NJ vieja (a destruir) | $103 ⚠️ |
| Cloudflare Free | $0 |
| **Total actual** | **$151/mo** ⚠️ |
| **Total objetivo (post cleanup)** | **$24/mo** |

**Acción urgente:** destroy NJ + snapshot vieja → ahorra $127/mo.

---

## Próximos pasos (orden de impacto)

1. ~~**WAF custom rules**~~ ✅ DONE (5 rules: scanner UA block, recon paths, geo, admin lockdown, rate limit 50/10s)
2. ~~**Admin lockdown**~~ ✅ DONE (WAF rule allow only operator IP en `traefik`/`grafana` + Traefik basicauth)
3. **Cleanup costos** — destroy VPS NJ ($103/mo) + snapshot 480GB ($24/mo) → $127/mo savings ⚠️ pendiente
4. **Update `GONXA-BRIEFING.md`** con target v2 + ROE actualizado
5. **WG client config** + SSH UFW lockdown — defensa-en-profundidad
6. **Re-scope docs/** v1 a v2 (incremental)
7. **Engagement Gonxa v2** kickoff cuando todo arriba esté ✅

## Inteligencia adquirida sobre el atacante (Leviathan 8.2)

Análisis profundo en este repo no público (`leviathan-claude-code/`):
- **Arsenal:** 285 módulos Python, 250K LOC, 1179 payloads, 30 attack chains
- **Bypass WAF:** detección de 10 vendors (Cloudflare/Akamai/Imperva/AWS/etc), matriz 21 técnicas encoding, adaptive learning loop con binary search
- **Cobertura:** OWASP Web/API/LLM completos (LLM01-LLM10), SQLi 99 payloads × 6 engines, JWT 8 clases ataque, SSRF 7 clouds × 14 loopback variants
- **Modes:** STEALTH (1 payload/param) → TACTICAL → WARFARE (todos × encoding × bypasses × 8 Opus paralelos)
- **Costo 24h WARFARE:** $290-570 USD (Opus 4.6/4.7 swarm + auto-chain)
- **Track record:** comprometió Akua.la (fintech con cliente Itaú Bank) — engagement AKUA-002 documentado, Buenos Aires Gob (Drupal 8 EOL)

### Probabilidades vs defensa actual melispy.com

| Objetivo Leviathan | Probabilidad | Notas |
|---|---|---|
| Enumerar todos subdomains | **95%+** | crt.sh + bruteforce, pasivo, nada lo detiene |
| Pasar Cloudflare WAF | **75-85%** WARFARE | 5 técnicas específicas CF + adaptive learning |
| Encontrar honeytokens leakeados | **90%+** | js_secret_extractor S-grade |
| Prompt injection AI agent (DVAIA) | **70-80%** | 50+ payloads LLM + 11-step chain |
| Lateral cross-stack post-foothold | **60-75%** | pivot_engine multi-hop + cred reuse |
| **Detectar canary paths sin caer** | **25-40%** | Punto débil — usará tokens sin distinguir trampa |

**Conclusión:** challenge moderado actual. Para ser challenge real necesita hardening adicional (recomendaciones abajo).

### Pivot 2026-04-25 — military-grade posture (v3)

Tras el análisis Leviathan, decisión: **eliminar TODO honeytoken regalado**. Lab pasa a posture realista de target prod hardened. Vulns retenidas pero **post-auth únicamente**.

### Cambios v2 → v3

| Cambio | Razón |
|---|---|
| Removidos honeytokens del landing HTML | Era CTF-style, no realista |
| Removidos canary paths del robots.txt (ahora `Disallow: /` minimal) | Lo mismo |
| Removido sitemap.xml entero | No agrega valor en prod real |
| Removidos `/docs` `/redoc` `/openapi.json` en TODAS las apps FastAPI | Real prod los disabilita |
| `/health` reducido a `{"status":"ok"}` | Sin debug fields, sin service name |
| `Mobile BFF` removed `debug_api_key` from /health | Era spoiler obvio |
| `DVAIA` removed AGENT_SECRETS leak en SYSTEM_CONTEXT response | Era spoiler obvio |
| `PromptMe` removed system_prompt leak in /admin/prompts | Era endpoint regalado |
| Auth gate JWT en todos los endpoints reales | Sin auth, no hay attack surface real |
| 404 generic uniforme (no 401 vs 404 oracle) | Anti-enumeration |
| Drop alias subdomains: ai/assistant/saas/app/store/lab/gt | Reduce recon hints |
| Rate limit 50 → **25 req/10s** | Más agresivo, anti-WARFARE |

### Vulns retenidas (post-auth)

Todo el resto de vulnerabilidades sigue intacto, pero solo accesibles después de pasar auth gate:

- JWT alg=none accepted (mobile, dvaia, promptme, tenant)
- JWT HS256 weak secret brute-forceable
- BOLA en `tenant.melispy.com` (cross-tenant)
- IDOR en `mobile.melispy.com /v1/users/{id}`
- Tool RCE post-auth en `agent.melispy.com /v1/chat` (tool_call dispatch)
- Prompt injection post-auth + XFF spoof en `chat.melispy.com`
- Login uid downgrade en mobile (forja JWT con uid=3 = admin)
- Invitation token predictable 4-byte hex en tenant
- OWASP Juice Shop full top 10 en `shop.melispy.com`

## Defensa vigente (post WAF)

| Layer | Mecanismo | Estado |
|---|---|---|
| Edge | CF WAF rule 1: bloquea sqlmap/nikto/nuclei/gobuster/dirb/feroxbuster/wfuzz/ffuf/masscan UAs | ✅ |
| Edge | CF WAF rule 2: challenge UA empty/curl/wget/python-requests | ✅ |
| Edge | CF WAF rule 3: bloquea `/.git/`, `/.env`, `/wp-admin/install.php`, `/phpmyadmin`, `/.aws/`, `/.ssh/` | ✅ |
| Edge | CF WAF rule 4: geo block KP/IR/BY | ✅ |
| Edge | CF WAF rule 5: `traefik.*` y `grafana.*` solo desde `179.24.190.234` | ✅ |
| Edge | CF Rate Limit: 50 req / 10s per IP per colo, action block, mitigación 10s | ✅ |
| Edge | DNS sin wildcard (anti-recon) | ✅ |
| Edge | Cloudflare Tunnel egress only (cero IP pública entrante a apps) | ✅ |
| App | Traefik middleware: ratelimit + security-headers + strip-server | ✅ |
| App | Traefik admin: IP allowlist + basic auth | ✅ |
| Net | UFW default-deny (port 22 abierto temporal a all + key-only auth) | ✅ |
| Net | fail2ban: jail SSH (ya baneó 1 atacante hoy automáticamente) | ✅ |
| OS | sysctl kernel hardening, auditd, AIDE FIM, lynis | ✅ |
| Container | userns OFF (compat), no-new-privileges ON, networks aisladas (mgmt/attacker/target) | ✅ |
| Container | target_net `internal: true` (GTs sin egress directo) | ✅ |

---

## Estructura repo (post-reorg v2)

```
leviathan-sparring-lab/
├── STATE.md                      ← este doc (resumen mental)
├── HANDOFF.md                    ← session state Claude
├── README.md                     ← quickstart + status
├── vultr-deploy-plan.md          ← plan v2 detallado (source of truth)
├── GONXA-BRIEFING.md             ← briefing engagement (a actualizar)
├── docker-compose.lean.yml       ← stack v2 (11 containers)
├── Makefile                      ← targets v2 (up/down/rotate/harden/audit/logs)
├── .env.lab                      ← credenciales + IP (gitignored)
│
├── deploy/
│   ├── landing/index.html        ← decoy SaaS page
│   ├── traefik/dynamic/          ← middleware (rate limit, headers, kill-switch)
│   ├── observability/            ← loki + promtail + grafana provisioning
│   ├── falco/                    ← rules custom anti-Gonxa TTPs
│   └── seccomp/                  ← Docker seccomp profile
│
├── targets/                      ← 36 GT catálogo
│   ├── catalog.yml               ← metadata (CVE, severity, gonxa_pain)
│   ├── damn-vulnerable-ai-agent/ ← AI agent FastAPI ✅ deployed
│   ├── promptme/                 ← LLM injection ✅ deployed
│   ├── tenant-billing-api/       ← SaaS multi-tenant ✅ deployed
│   ├── mobile-backend-weak/      ← Mobile BFF ✅ deployed
│   └── <33 más>/                 ← catálogo, no deployados
│
├── scripts/
│   ├── lab-up.sh                 ← bootstrap deploy
│   ├── lab-down.sh               ← snapshot+destroy lifecycle
│   ├── gt-rotate.sh              ← swap GT activo
│   ├── harden.sh                 ← idempotent OS hardening (9 phases)
│   └── <utility scripts>
│
├── terraform/                    ← Cloudflare provisioning (CF-only)
├── ground_truth/                 ← 131 entries para scoring
├── engagements/                  ← per-engagement evidence
├── docs/                         ← documentación (incremental re-scope)
└── legacy/                       ← v1 archivado (destroy tras 2-3 corridas v2 OK)
```

---

## Pre-engagement Gonxa checklist (cuando empiece)

- [ ] WAF activa + custom rules
- [ ] CF Access en admin panels
- [ ] Snapshot pre-engagement Vultr (rollback safety)
- [ ] AIDE baseline reset
- [ ] Falco + CrowdSec opcionales activados
- [ ] `engagements/LEV-MELISPY-GONXA-002/` directorio creado
- [ ] Kill-switch verificado (`/kill-switch` path responde 503)
- [ ] Loki dashboard `pentest-overview` creado
- [ ] `lab.yaml` ROE engagement-specific creado
- [ ] `GONXA-BRIEFING.md` v2 enviado a Gonxa
- [ ] Window 24h agendado
- [ ] Leviathan UI laptop arriba `bun run web`
