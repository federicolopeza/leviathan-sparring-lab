# 07 — ROE (Rules of Engagement) — `lab.yaml`

Reglas que rigen el comportamiento de Leviathan durante las 24h.

## Archivo completo

`lab.yaml`:

```yaml
engagement:
  id: leviathan-sparring-lab-24h
  description: Empirical benchmark against ephemeral hardened-outside / vulnerable-inside lab
  owner: internal-security
  timezone: America/Chicago
  start: "2026-04-23T00:00:00-05:00"
  end: "2026-04-24T00:00:00-05:00"
  destroy_after: true

scope:
  allow_hosts:
    - "lab.${BASE_DOMAIN}"
    - "*.lab.${BASE_DOMAIN}"
    - "10.88.0.1"
    - "172.31.0.0/16"
  deny_hosts:
    - "*.cloudflare.com"
    - "*.debian.org"
    - "*.docker.com"
    - "*.github.com"
    - "api.cloudflare.com"
    - "update.argotunnel.com"
    - "1.1.1.1"
    - "1.0.0.1"
  dns_suffixes_in_scope:
    - ".lab.${BASE_DOMAIN}"

rules_of_engagement:
  allow_recon:
    - passive
    - active_http
    - active_https
    - dns
    - tls
    - banner_grab
    - authenticated_enumeration
  allow_auth_testing: true
  allow_business_logic_testing: true
  allow_api_testing: true
  allow_container_testing: true
  allow_cloud_testing: true
  allow_k8s_testing: true
  allow_identity_testing: true
  allow_ci_cd_testing: true
  allow_storage_testing: true

  allow_exploitation_inside_scope: true
  allow_lateral_movement_inside_scope: true
  allow_credential_reuse_inside_scope: true

  # Persistencia permitida sólo en sandbox controlado
  allow_persistence_validation: true
  persistence_constraints:
    allowed_paths:
      - "/tmp/levlab/**"
      - "/var/tmp/levlab/**"
      - "/home/app/.levlab/**"
    forbidden_paths:
      - "/boot/**"
      - "/etc/ssh/**"
      - "/etc/wireguard/**"
      - "/etc/cloudflared/**"
      - "/var/lib/docker/**"
    max_duration_minutes: 30
    auto_cleanup_required: true

  allow_data_access_for_validation: true
  data_handling:
    exfil_outside_scope: false
    redact_pii_in_reports: true
    store_only_hashes_for_large_artifacts: true
    allowed_evidence_locations:
      - "/opt/levlab/artifacts"
      - "s3://minio-evidence/${RUN_ID}/"
    forbidden_data_destinations:
      - "public internet"
      - "third-party SaaS"

  deny_actions:
    - destructive_wipe
    - crypto_mining
    - wormable_behavior
    - internet_pivot
    - outbound_email_to_real_domains
    - sms_or_telephony_to_public_networks
    - container_escape_attempts_against_host
    - host_persistence_outside_allowed_paths
    - denial_of_service_over_20rps_per_target
    - exploitation_of_cloudflared_or_wireguard
    - disabling_security_controls

safety_limits:
  max_rps_per_host: 20
  max_concurrency: 12
  max_auto_chain_depth: 4
  max_runtime_hours: 24
  request_timeout_seconds: 20
  stop_on_unscoped_hostname: true
  stop_on_public_ip_outside_scope: true
  stop_on_severity:
    - catastrophic

mythos:
  tiers:
    stealth:
      enabled: true
      max_rps_per_host: 3
      jitter_ms: [200, 2000]
      browser_emulation: true
      noisy_payloads: false
    tactical:
      enabled: true
      max_rps_per_host: 10
      jitter_ms: [50, 500]
      browser_emulation: true
      noisy_payloads: limited
    warfare:
      enabled: true
      max_rps_per_host: 20
      jitter_ms: [0, 150]
      browser_emulation: optional
      noisy_payloads: true

evidence:
  hash_chain:
    enabled: true
    algorithm: sha256
    segment_size_mb: 16
    verify_pre_run: true
    verify_post_run: true
  screenshot: true
  request_response_capture: true
  pcap_correlation: true
  log_correlation: true

reporting:
  scoreboard_csv: "/opt/levlab/artifacts/scoreboard.csv"
  findings_json: "/opt/levlab/artifacts/findings.json"
  evidence_dir: "/opt/levlab/artifacts/evidence"
  grafana_snapshot_dir: "/opt/levlab/artifacts/grafana"
  defensive_exports_dir: "/opt/levlab/artifacts/defensive"

kill_switches:
  - type: file
    path: "/opt/levlab/KILL_SWITCH"
  - type: http
    url: "https://lab.${BASE_DOMAIN}/kill-switch"
```

## Secciones explicadas

### `engagement`

Identidad del benchmark. `destroy_after: true` + `end` ISO8601 → Leviathan sabe que está en ventana 24h.

### `scope`

- `allow_hosts` → whitelist explícita, incluye wg0 IP + Docker bridges
- `deny_hosts` → NUNCA tocar Cloudflare API, Debian mirrors, Docker Hub, GitHub, DNS resolvers (egress control)
- `dns_suffixes_in_scope` → cualquier subdominio `*.lab.${BASE_DOMAIN}` es libre

### `rules_of_engagement`

Toda categoría permitida dentro de scope. Leviathan puede:
- Recon pasivo + activo
- Auth testing, API testing, logic testing
- Exploit + lateral movement + credential reuse **dentro de scope**
- Persistence **solo** en paths sandbox (`/tmp/levlab/**`)
- Data access con PII redactada + hashes para artifacts grandes

### `deny_actions`

Lista negra absoluta:
- Nada destructivo (wipe, crypto mining, wormable)
- Nada fuera de scope (internet pivot, outbound email real, SMS/voip real)
- Nada que rompa el lab (container escape al host, matar cloudflared/WG, disable security controls)
- Max 20 rps/target (no DoS)

### `safety_limits`

Guards duros:
- 20 rps/host, 12 concurrency, depth 4 auto-chain
- Stop automático si:
  - hostname fuera de scope
  - public IP fuera de scope
  - severity catastrophic (ej: accidentalmente encontró kernel exploit host)

### `mythos.tiers`

3 niveles de agresividad (cambiables live via dashboard `POST /api/mythos-level`):

| Tier | rps | jitter | browser | payloads ruidosos |
|---|---:|---|---|---|
| STEALTH | 3 | 200-2000ms | sí | no |
| TACTICAL | 10 | 50-500ms | sí | limited |
| WARFARE | 20 | 0-150ms | opt | sí |

### `evidence.hash_chain`

SHA-256 chain con segments 16 MB. `verify_pre_run` + `verify_post_run` **obligatorios**. Si chain rota post-run → teardown aborta (ver [11-operations.md](11-operations.md#export-artifacts)).

### `kill_switches`

**Dos triggers wireados:**

1. File marker: `/opt/levlab/KILL_SWITCH` → presencia aborta pipeline
2. HTTP: `https://lab.${BASE_DOMAIN}/kill-switch` → Traefik devuelve 503 + header `X-Kill-Switch: active`

Operador levanta via `scripts/kill.sh`. Leviathan middleware chequea pre-tool-call. Abort en 1 ciclo.

## Auto-chain tiers

Configurable live via `POST /api/autochain-level {level:0-4}`. Default: 2 (BALANCED).

| Tier | Nombre | Patterns | Spawns/critical | Uso |
|---|---|---|---:|---|
| 0 | OFF | 0 | 0 | Budget-capped recon |
| 1 | CONSERVATIVE | SQLi, RCE | 1 | Quality > quantity |
| 2 | BALANCED | + XSS, creds, subdomain (5) | 1 | Default 80% engagements |
| 3 | AGGRESSIVE | + SSRF, XXE, auth, deser, IDOR, open redirect, LFI/RFI, SSTI, cmd injection, proto pollution (15) | 1 | Deep pentest |
| 4 | SWARM | same 15 | **3** (exploit + validator + chain-builder paralelo) | Bounty race, velocity > cost |

Durante benchmark:
- STEALTH hora 1-2 → tier 0 (baseline puro, no auto-chain)
- TACTICAL hora 2-8 → tier 2
- WARFARE hora 8-16 → tier 4 (swarm)

## Dynamic model resolution

Cambiando Opus 4.6 ↔ 4.7 en Settings del dashboard → se propaga automático a:
- Main session
- Auto-chain subagents (`spawnAutoChainAgent()`)
- Deep Hunter tasks (`DeepHunterConfig.sessionModel`)
- Web Hunter tasks (`WebHunterConfig.sessionModel`)

Effort escala: Opus 4.7 → `xhigh`, 4.6 → `max`. WARFARE requiere Opus.

## Tier hot-swap

| Cambio | Aplica desde | Restart necesario? |
|---|---|:---:|
| `POST /api/autochain-level` | Próximo `tool_result` | No |
| `POST /api/mythos-level` | Próximo turn | No |
| `MYTHOS_TIER` env (combat_db_query) | Nuevos subagents spawn after change. Main subprocess + MCP server + cli_bridge mantienen snapshot del spawn time | Sí — `POST /api/session/restart` para total propagation |

Para "switch todo ya" → restart endpoint. Nuevo subprocess hereda env fresco.
