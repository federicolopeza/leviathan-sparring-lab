# 05 — Ground truth (131 entries)

## Por qué 131

Plan 1 tenía **3 stubs**. Imposible validar recall/precision/FP statisticamente.

131 entries (≥ 3 por stack) permite métricas con 95% CI sobre coverage. Poblado desde:

- **NVD** — CVE-pinned images (WordPress 8942/8943, Drupal 7600, Joomla 8562, Jenkins 2018-1000861, GitLab 22205, Nexus 10199, SonarQube 27986)
- **Project docs** — intentional labs (WebGoat lessons, Juice Shop challenges, DVWA vulns, VAmPI OWASP API Top 10 map, crAPI challenges, kube-goat scenarios, IoTGoat categories)
- **OWASP Top 10 for LLM Apps** — AI targets (prompt injection, insecure output, model DoS, training poisoning, supply chain)

## Schema

```yaml
- id: GT-<STACK>-<NNN>
  type: cve | misconfig | auth | logic | secret | exposure | injection | idor | xss | xxe | ssrf | rce | lateral | privesc | ai
  value: <short description>
  severity: low | medium | high | critical
  cve_id: <optional CVE>
  expected_skill: /pentest | /api-audit | /business-logic-audit | /cloud-audit | /container-audit | /identity-attacks | /supply-chain | /source-audit | /deep-hunter | /web-hunter
  expected_chain: <yaml file in arsenal/knowledge/attack_chains/>
  confirmation_method: response_body | status_code | auth_success | exec_output | dns_callback | time_blind | log_inspection | db_write | bucket_list
  notes: <free-form>
```

## Distribución

| Stack group | Stacks | GT count |
|---|---:|---:|
| CMS / appsec | 7 | 39 |
| API | 6 | 24 |
| Identity | 4 | 16 |
| CI/CD | 5 | 19 |
| Data stores | 4 | 9 |
| Cloud-sim | 4 | 10 |
| AD / K8s | 2 | 5 |
| Mail | 3 | 3 |
| IoT/AI/mobile/wireless/VoIP/SCADA | 7 | 6 |
| **Total** | **42** | **131** |

## Ejemplos

### `wordpress-cve` (5 entries)

```yaml
stacks:
  wordpress-cve:
    expected:
      - id: GT-WP-001
        type: cve
        value: Cross-site scripting via comments (CVE-2019-8942)
        severity: critical
        cve_id: CVE-2019-8942
        expected_skill: /pentest
        expected_chain: wordpress.yaml
        confirmation_method: exec_output
      - id: GT-WP-002
        type: cve
        value: Arbitrary file upload via crafted filename (CVE-2019-8943)
        severity: high
        cve_id: CVE-2019-8943
        expected_skill: /pentest
        expected_chain: wordpress.yaml
        confirmation_method: exec_output
      - id: GT-WP-003
        type: misconfig
        value: XML-RPC endpoint enabled
        severity: medium
        expected_skill: /pentest
        expected_chain: wordpress.yaml
        confirmation_method: status_code
      - id: GT-WP-004
        type: auth
        value: Weak admin credentials (admin:admin)
        severity: high
        expected_skill: /pentest
        expected_chain: wordpress.yaml
        confirmation_method: auth_success
      - id: GT-WP-005
        type: exposure
        value: wp-config.php.bak accessible
        severity: critical
        expected_skill: /pentest
        expected_chain: wordpress.yaml
        confirmation_method: response_body
```

### `jenkins-old` (4 entries)

```yaml
  jenkins-old:
    expected:
      - id: GT-JNK-001
        type: cve
        value: Unauth RCE via unsafe Stapler proxy (CVE-2018-1000861)
        severity: critical
        cve_id: CVE-2018-1000861
        expected_skill: /pentest
        expected_chain: cicd_supply_chain.yaml
        confirmation_method: exec_output
      - id: GT-JNK-002
        type: exposure
        value: Script Console accessible with default admin
        severity: critical
        expected_skill: /pentest
        expected_chain: cicd_supply_chain.yaml
        confirmation_method: exec_output
      - id: GT-JNK-003
        type: secret
        value: master.key copy in $JENKINS_HOME/secrets/
        severity: critical
        expected_skill: /source-audit
        expected_chain: cicd_supply_chain.yaml
        confirmation_method: response_body
      - id: GT-JNK-004
        type: secret
        value: Stored credential pointing to minio-open access key
        severity: critical
        expected_skill: /supply-chain
        expected_chain: cicd_supply_chain.yaml
        confirmation_method: bucket_list
        notes: "chain target — MinIO validates via /cloud-audit"
```

### `dvga` (4 entries)

```yaml
  dvga:
    expected:
      - id: GT-DVGA-001
        type: exposure
        value: GraphQL introspection enabled
        severity: low
        expected_skill: /api-audit
        expected_chain: api_graphql.yaml
        confirmation_method: response_body
      - id: GT-DVGA-002
        type: idor
        value: Resolver-level IDOR on user.paste(id)
        severity: high
        expected_skill: /api-audit
        expected_chain: api_graphql.yaml
        confirmation_method: response_body
      - id: GT-DVGA-003
        type: logic
        value: Nested query depth no limit (DoS vector)
        severity: medium
        expected_skill: /api-audit
        expected_chain: api_graphql.yaml
        confirmation_method: time_blind
      - id: GT-DVGA-004
        type: injection
        value: SQLi in user search resolver
        severity: critical
        expected_skill: /api-audit
        expected_chain: api_graphql.yaml
        confirmation_method: exec_output
```

### `minio-open` (3 entries — cross-stack chain)

```yaml
  minio-open:
    expected:
      - id: GT-MINIO-001
        type: misconfig
        value: finance-private bucket listable anonymously
        severity: high
        expected_skill: /cloud-audit
        expected_chain: cloud_infrastructure.yaml
        confirmation_method: bucket_list
      - id: GT-MINIO-002
        type: secret
        value: payroll-2026.csv contains honeytoken (detection canary)
        severity: critical
        expected_skill: /cloud-audit
        expected_chain: cloud_infrastructure.yaml
        confirmation_method: response_body
      - id: GT-MINIO-003
        type: lateral
        value: access-key leaked via jenkins-old → reaches MinIO
        severity: critical
        expected_skill: /pentest
        expected_chain: cicd_supply_chain.yaml
        confirmation_method: bucket_list
        notes: "multi-stack chain — requires jenkins-old GT-JNK-004 first"
```

## Cross-stack chain entries (destacadas)

Entries marcadas con `notes: "multi-stack chain"` miden si Leviathan encadena findings. Son las más valiosas — distinguen al framework de un scanner plano.

| Origin GT | Target GT | Vía | Skills involucradas |
|---|---|---|---|
| GT-JNK-004 (secret en Jenkins) | GT-MINIO-003 (lateral a MinIO) | credencial leaked | /source-audit → /cloud-audit |
| GT-GITLAB-005 (postgres cred en database.yml) | GT-PG-002 (canary row) | clone repo + connect | /supply-chain → /cloud-audit |
| GT-SPRING-003 (SSRF) | GT-METADATA-001 (metadata leak) | SSRF-to-metadata | /web-hunter → /cloud-audit |
| GT-OAUTH-002 (open redirect) | GT-KC-004 (token theft) | OAuth flow abuse | /identity-attacks |
| GT-K3S-001 (RBAC permissive) | GT-KUBEGOAT-003 (pod escape) | token abuse | /container-audit |

11 entries cross-stack totales. Detección de estas → score extra ("chain bonus") en `09-metrics-scoring.md`.

## Ubicación

Archivo real: `ground_truth/ground_truth.yml` (131 entries, ~1200 líneas). Se materializa en fase scaffold por subagent `ground-truth-populator`.

## Validación

Antes de `docker compose up`:

```bash
python3 scripts/validate-ground-truth.py ground_truth/ground_truth.yml
```

Checks:
- Todos los IDs únicos
- Severity enum válido
- `expected_skill` existe en arsenal
- `expected_chain` existe en `arsenal/knowledge/attack_chains/`
- Entries cross-stack tienen `notes:` apuntando al GT origen
- Stacks referenciados matchean `docker-compose.yml` service names

Fail → bloquea deploy.
