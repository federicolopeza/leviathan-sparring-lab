# Postmortem — Leviathan Sparring Lab

## 1. Resumen ejecutivo

- Run ID:
- Fecha:
- Duración:
- Provider: Vultr (vhp-8c-16gb-amd, region=___)
- VPS IP:
- Commit Leviathan:
- ROE version:
- Ground truth version:

## 2. Cobertura Leviathan

| Métrica | Valor |
|---|---:|
| Ground truth total | 131 |
| Detectados |  |
| Explotados |  |
| Coverage rate |  |
| Exploit rate |  |
| False negatives |  |
| False positivos estimados |  |
| Chain bonus (cross-stack) |  / 11 |

## 3. Cobertura por chain (28 chains)

| Chain | GT total | Detectados | Explotados | Cobertura | Notas |
|---|---:|---:|---:|---:|---|
| generic_web |  |  |  |  |  |
| api_rest |  |  |  |  |  |
| api_graphql |  |  |  |  |  |
| wordpress |  |  |  |  |  |
| django |  |  |  |  |  |
| rails |  |  |  |  |  |
| spring |  |  |  |  |  |
| node |  |  |  |  |  |
| php |  |  |  |  |  |
| go |  |  |  |  |  |
| dotnet |  |  |  |  |  |
| juice_shop |  |  |  |  |  |
| exchange |  |  |  |  |  |
| mail_server |  |  |  |  |  |
| active_directory |  |  |  |  |  |
| cloud_infrastructure |  |  |  |  |  |
| cicd_supply_chain |  |  |  |  |  |
| zero_day_research |  |  |  |  |  |
| iot_embedded |  |  |  |  |  |
| bug_bounty |  |  |  |  |  |
| mobile_pentest |  |  |  |  |  |
| wireless_pentest |  |  |  |  |  |
| saas_exploitation |  |  |  |  |  |
| ai_ml_attacks |  |  |  |  |  |
| voip_scada |  |  |  |  |  |
| advanced_web |  |  |  |  |  |
| identity_attacks |  |  |  |  |  |
| container_kubernetes |  |  |  |  |  |

## 4. Comparativa STEALTH vs TACTICAL vs WARFARE

| Métrica | STEALTH | TACTICAL | WARFARE |
|---|---:|---:|---:|
| Findings totales |  |  |  |
| Findings críticos |  |  |  |
| Exploits exitosos |  |  |  |
| Time-to-first-critical |  |  |  |
| WAF blocks sufridos |  |  |  |
| Auto-chain depth promedio |  |  |  |
| Evidence hash integrity |  |  |  |

**Interpretación:**
- Gain T→W (findings): __
- Gain T→W (críticos): __
- Gain T→W (exploits): __
- Costo W/T ratio: __

## 5. Tiempo por fase

| Fase | Inicio | Fin | Duración |
|---|---|---|---|
| Deploy + smoke |  |  |  |
| STEALTH baseline |  |  |  |
| TACTICAL run |  |  |  |
| WARFARE run |  |  |  |
| Chaos mode |  |  |  |
| Defensive analysis |  |  |  |
| Teardown |  |  |  |

## 6. WAF bypass vs Cloudflare real

- Managed rules triggered:
- OWASP CRS triggers:
- Custom rule actions:
- Éxitos de reaching-origin:
- Requests bloqueados en edge:
- Requests bloqueados en ModSec local:
- Casos donde WAF frenó explotación pero dejó evidencia defensiva suficiente:
- WAF bypass success rate per vendor family:

| Vendor family | Payloads sent | Blocked | Bypassed | Bypass rate |
|---|---:|---:|---:|---:|
| Cloudflare Managed |  |  |  |  |
| OWASP CRS PL2 |  |  |  |  |
| ModSec local |  |  |  |  |

## 7. False positive rate por skill

| Skill | Findings | Confirmados | FPs | FP rate |
|---|---:|---:|---:|---:|
| /pentest |  |  |  |  |
| /api-audit |  |  |  |  |
| /business-logic-audit |  |  |  |  |
| /identity-attacks |  |  |  |  |
| /cloud-audit |  |  |  |  |
| /container-audit |  |  |  |  |
| /supply-chain |  |  |  |  |
| /source-audit |  |  |  |  |
| /deep-hunter |  |  |  |  |
| /web-hunter |  |  |  |  |
| /waf-bypass |  |  |  |  |

## 8. Gaps detectados

### 8.1 Gaps de cobertura

- Chain: <chain_name>
  Stack: <stack>
  GT no detectada: <GT-ID>
  Hipótesis: <por qué falló>
  Prioridad: low | medium | high | critical

### 8.2 Gaps de explotación

- Finding detectado pero no explotado: <F-ID>
  Restricción: <WAF block / rate limit / payload incompleto>
  Skill afectada: </skill-name>
  Ticket sugerido: <arsenal/path/to/module>

## 9. Tickets para `arsenal/`

- arsenal/modules/<name> — <descripción del fix>
- arsenal/knowledge/attack_chains/<chain> — <qué agregar>
- arsenal/skills/<skill> — <cambio de heurística>
- arsenal/evidence/<module> — <mejora en captura>
- arsenal/dashboard/<view> — <nueva métrica a mostrar>

## 10. Evidencia y verificación

- findings.json.sha256:
- scoreboard.csv.sha256:
- hash-chain verify result: OK / BROKEN
- pcap snapshot:
- grafana snapshots:
- defensive exports:

## 11. Token economics per Mythos tier

**Fuente:** `engagements/$RUN_ID/cost-report.json` + `skill-telemetry.jsonl`.

### 11.1 Per-tier cost breakdown

| Tier | Input tokens | Output tokens | Cache read | Cache write | USD total | Findings | USD / finding | Findings / USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| STEALTH |  |  |  |  | $ |  | $ |  |
| TACTICAL |  |  |  |  | $ |  | $ |  |
| WARFARE |  |  |  |  | $ |  | $ |  |
| **Total** |  |  |  |  | $ |  | | |

### 11.2 Ratio validation

**Hipótesis:** WARFARE debe dar **>= 3x findings/hora** y **>= 2x unique critical findings** vs TACTICAL para justificar 3-5x costo en tokens.

- WARFARE findings/hora: __ vs TACTICAL: __ -> ratio __
- WARFARE unique critical: __ vs TACTICAL: __ -> ratio __
- **Verdict:** WARFARE justified / not justified en este target profile

### 11.3 Per-skill cost ranking

| Skill | Avg tokens/run | USD/run | Findings/run | USD/finding |
|---|---:|---:|---:|---:|
| /pentest |  |  |  |  |
| /api-audit |  |  |  |  |
| /business-logic-audit |  |  |  |  |
| /identity-attacks |  |  |  |  |
| /cloud-audit |  |  |  |  |
| /container-audit |  |  |  |  |
| /supply-chain |  |  |  |  |
| /source-audit |  |  |  |  |
| /deep-hunter |  |  |  |  |
| /web-hunter |  |  |  |  |
| /waf-bypass |  |  |  |  |

### 11.4 Cache hit rate

**Target:** >= 60% cache read ratio en TACTICAL+WARFARE (prompt caching system + ROE + context).

- Observed: __ %
- Si < 60%: recomendaciones para futuras corridas

### 11.5 Total cost analysis

Infra (Vultr + bw):                $ ___
Tokens Opus total:                 $ ___
Total run:                         $ ___
Cost per critical finding:         $ ___
Cost per exploited vuln:           $ ___
Target: < $1/critical finding      [PASS / FAIL]
Target: < $3/exploit               [PASS / FAIL]
