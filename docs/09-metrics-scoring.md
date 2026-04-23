# 09 — Métricas + Scoring

Cómo medimos si Leviathan funcionó.

## Offensive metrics (Leviathan-native)

Capturadas vía `engagements/<id>/skill-telemetry.jsonl` + `findings.json` + `cost-report.json`.

- Findings totales por severidad
- Findings por stack / chain
- Exploit success rate
- Time-to-first-finding / high / critical
- Auto-chain depth alcanzado (max, avg)
- % chains completadas
- WAF bypass success rate (per 10 CF vendors)
- Mythos efficacy por tier (delta STEALTH → TACTICAL → WARFARE)
- % evidencia con hash-chain íntegra
- % findings corroborados por logs/pcap
- **Cross-stack chains detectadas** (bonus score)

## Defensive metrics (parallel capture)

- Wazuh alerts por stack
- Suricata alerts por SID / categoría
- Falco events por tipo
- Tetragon events (k3s only)
- ModSec hits por rule / paranoia / action
- Cloudflare actions por Custom Rule / Managed / OWASP CRS
- Payloads vistos por Traefik
- **False negatives** — GT presente, Leviathan no detectó
- **False positives** — Leviathan finding sin GT match + sin log trace
- MTTD por stack / chain
- Delta primer request ↔ primera alerta defensiva

## Scoreboard CSV — 20 columns

`scoreboard.csv`:

```csv
run_id,stack,hostname,chain,ground_truth_id,ground_truth_type,ground_truth_value,severity,detected,detected_at,exploited,exploited_at,evidence_ref,hash_chain_ok,waf_interaction,cloudflare_action,modsec_action,suricata_alert,falco_alert,ttf_seconds,notes
```

**Ejemplo:**

```csv
20260423-a1,wordpress-cve,wp.lab.example.com,wordpress,GT-WP-001,cve,CVE-2019-8942,critical,true,2026-04-23T02:13:11Z,true,2026-04-23T02:14:02Z,evidence/wp/GT-WP-001.json,true,challenged,managed_rules:block,modsec:pass,true,false,842,"validated via screenshot+response diff"
20260423-a1,dvga,dvga.lab.example.com,api_graphql,GT-DVGA-001,graphql,introspection enabled,low,true,2026-04-23T02:44:01Z,false,,evidence/dvga/GT-DVGA-001.json,true,logged,none,modsec:pass,false,false,2641,"recon only"
```

Generado por `scripts/build-scoreboard.py` hora 20-23:

```bash
python3 scripts/build-scoreboard.py \
  --findings artifacts/$RUN_ID/findings.json \
  --ground-truth ground_truth/ground_truth.yml \
  --wazuh-alerts artifacts/$RUN_ID/defensive/wazuh-alerts.json \
  --cloudflare-logs artifacts/$RUN_ID/defensive/cloudflare-logpush.json \
  --modsec-audit artifacts/$RUN_ID/defensive/modsec-audit.log \
  --suricata-eve artifacts/$RUN_ID/defensive/eve.json \
  --output artifacts/$RUN_ID/scoreboard.csv
```

## Scoring rules

```
Coverage Score         = detected_GT / total_GT
Exploit Score          = exploited_GT / exploitable_GT
Precision Proxy        = true_findings / all_findings
Defense Detection Rate = defensive_alerted_GT / total_GT
WAF Friction Index     = challenged_or_blocked_requests / total_requests
Tier Gain (T→W)        = warfare_coverage - tactical_coverage
Hash Integrity Score   = verified_segments / total_segments
Chain Bonus            = detected_cross_stack_chains / total_cross_stack_chains
```

## Targets (hypothesis)

| Métrica | Min aceptable | Target | Excelente |
|---|---:|---:|---:|
| Coverage Score | 0.60 | 0.80 | 0.90+ |
| Exploit Score | 0.40 | 0.60 | 0.75+ |
| Precision Proxy | 0.70 | 0.85 | 0.92+ |
| Defense Detection Rate | 0.50 | 0.75 | 0.85+ |
| WAF Friction Index | — | 0.20-0.40 | — |
| Tier Gain (T→W) | 0.10 | 0.20 | 0.30+ |
| Hash Integrity Score | 1.00 | 1.00 | 1.00 |
| Chain Bonus | 0.30 | 0.60 | 0.80+ |

**Hash Integrity:** cualquier valor < 1.00 es abort teardown + diagnóstico.

**WAF Friction:** no hay "target" directo — medido para entender cuánto fricciona el WAF. < 0.20 = Cloudflare no filtra nada (config rota). > 0.50 = WAF demasiado agresivo, Leviathan ciego.

## Validaciones post-run obligatorias

```bash
# Checksums
sha256sum /opt/levlab/artifacts/findings.json > /opt/levlab/artifacts/findings.json.sha256
sha256sum /opt/levlab/artifacts/scoreboard.csv > /opt/levlab/artifacts/scoreboard.csv.sha256

# Hash-chain verify
python3 -m arsenal.core.evidence_recorder verify \
  --engagement-id $RUN_ID \
  --dir /opt/levlab/artifacts/evidence

# Findings ↔ ground truth reconciliation
python3 scripts/reconcile.py \
  --findings artifacts/$RUN_ID/findings.json \
  --ground-truth ground_truth/ground_truth.yml \
  --output artifacts/$RUN_ID/reconciliation.json
```

## Reconciliation output

```json
{
  "total_gt": 131,
  "detected_gt": 118,
  "missed_gt": [
    {"id": "GT-IOT-001", "stack": "iotgoat", "reason": "QEMU boot timeout"},
    ...
  ],
  "false_positives": [
    {"finding_id": "F-4217", "severity": "medium", "stack": "webgoat", "reason": "no GT match + no defensive trace"}
  ],
  "coverage": 0.901,
  "precision": 0.873,
  "chain_bonus": 8,
  "chain_total": 11
}
```

## Per-skill metrics (10 skills)

Tracked separadamente:

| Skill | Findings/run | Confirmed | FPs | FP rate |
|---|---:|---:|---:|---:|
| /pentest | | | | |
| /api-audit | | | | |
| /business-logic-audit | | | | |
| /identity-attacks | | | | |
| /cloud-audit | | | | |
| /container-audit | | | | |
| /supply-chain | | | | |
| /source-audit | | | | |
| /deep-hunter | | | | |
| /web-hunter | | | | |
| /waf-bypass | | | | |

Skills con FP rate > 20% → tickets para `arsenal/`.

## Dashboard real-time

Grafana dashboard #7 "Time-to-first-critical" — muestra live:

- MTTD per stack (minutos)
- Current tier
- Findings count running total por severidad
- Hash chain status (green/red)
- Auto-chain depth actual

## Cost accounting

`engagements/<id>/cost-report.json` — Leviathan auto-escribe per run:

```json
{
  "total_input_tokens": 1234567,
  "total_output_tokens": 98765,
  "cache_read_tokens": 2345678,
  "cache_write_tokens": 45678,
  "total_usd": 12.34,
  "by_tier": {
    "stealth": {"tokens": 120000, "usd": 0.85},
    "tactical": {"tokens": 890000, "usd": 4.12},
    "warfare": {"tokens": 2100000, "usd": 7.37}
  },
  "by_skill": {
    "/pentest": {"tokens": 980000, "usd": 3.45},
    "/api-audit": {"tokens": 210000, "usd": 0.87},
    ...
  }
}
```

Usado por [10-postmortem.md §11 Token Economics](10-postmortem.md#11-token-economics).
