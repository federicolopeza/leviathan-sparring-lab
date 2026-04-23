# 04 — Zoo de targets (28 stacks)

Dos familias:

1. **Apps entrenamiento deliberadamente vulnerables** — ground truth por clase de vuln (SQLi, IDOR, XSS, etc.)
2. **Productos reales CVE-pinned** — ground truth por CVE específico

Todos los targets pinneados por digest `sha256:<hash>` (no `:latest`) o builds locales en `targets/<stack>/Dockerfile` con commit hash.

## Inventario maestro

### A. CMS / web clásico / appsec (7 stacks)

| Stack | Imagen/pin | CVE / benchmark | Chains | Ground truth |
|---|---|---|---|---|
| `wordpress-cve` | `lab/wordpress-cve8942:2026.04.23` | CVE-2019-8942/8943 + XML-RPC | wordpress, php, generic_web, advanced_web, bug_bounty | version fingerprint, user enum, XML-RPC, weak creds, upload RCE |
| `drupal-cve` | `lab/drupal-cve7600:2026.04.23` | CVE-2018-7600 | generic_web, advanced_web, bug_bounty | fingerprint, unauth RCE surface, admin paths |
| `joomla-cve` | `lab/joomla-cve8562:2026.04.23` | CVE-2015-8562 | generic_web, php, advanced_web | fingerprint, template injection/RCE, admin exposure |
| `dvwa` | `ghcr.io/digininja/dvwa@sha256:...` | intencional | php, generic_web, advanced_web | SQLi, XSS, CSRF, file upload, cmd injection |
| `bwapp` | `lab/bwapp:2026.04.23` | intencional | php, generic_web, advanced_web | XXE, SSTI-like, SQLi, XSS, auth flaws |
| `webgoat` | `webgoat/webgoat:v2025.3` | intencional | generic_web, advanced_web, bug_bounty | injection classes, access control, business logic, deser, XXE |
| `mutillidae` | `lab/mutillidae:2026.04.23` | intencional | php, generic_web | login bypass, XSS, SQLi, cmd exec |
| `juice-shop` | `bkimminich/juice-shop@sha256:...` | intencional | juice_shop, node, advanced_web, bug_bounty, saas_exploitation | JWT, XSS, NoSQLi, auth, IDOR, bucket leaks, logic |
| `django-goat` | `lab/djangogoat:2026.04.23` | intencional | django, generic_web, advanced_web | debug exposure, secret leak, authz bypass, SQLi, template |
| `railsgoat` | `lab/railsgoat:2026.04.23` | intencional | rails, generic_web, advanced_web | mass assignment, authz, SSRF, cmd exec, file upload |
| `spring-petclinic-vuln` | `lab/vuln-spring-petclinic:2026.04.23` | misconfig | spring, generic_web, advanced_web, zero_day_research | actuator, H2 console, IDOR, deser, SSRF, template |

### B. APIs / GraphQL / gRPC / Go / .NET (6 stacks)

| Stack | Imagen/pin | Chains | Ground truth |
|---|---|---|---|
| `vampi` | `lab/vampi:2026.04.23` | api_rest, go, mobile_pentest, saas_exploitation | OWASP API Top 10, BOLA, data exposure, rate limit, token weak |
| `dvga` | `lab/dvga:2026.04.23` | api_graphql, advanced_web | introspection, authz bypass, over-fetching, IDOR resolvers, depth abuse |
| `crapi` | `lab/crapi:2026.04.23` | api_rest, advanced_web, mobile_pentest, saas_exploitation | BOLA, mass assignment, auth flaws, logic, weak reset |
| `grpc-goat` | `lab/grpc-goat:2026.04.23` | go, api_rest, zero_day_research | reflection, insecure transport, auth gaps, proto enum leakage |
| `dotnet-goat` | `lab/dotnet-goat:2026.04.23` | dotnet, generic_web, advanced_web | deser, SSRF, file upload, IDOR, JWT mistakes |
| `go-fuzz-svc` | `lab/go-fuzz-svc:2026.04.23` | go, zero_day_research | panic surfaces, parser confusion, smuggling, debug endpoints |

### C. Identity / SAML / SaaS (4 stacks)

| Stack | Imagen/pin | Chains | Ground truth |
|---|---|---|---|
| `keycloak-weak` | `lab/keycloak-weak:2026.04.23` | saas_exploitation, identity_attacks | default realm leaks, weak clients, broad redirect URIs, admin exposed |
| `oauth-lab` | `lab/oauth-lab:2026.04.23` | saas_exploitation, identity_attacks, mobile_pentest | implicit flow misuse, no PKCE, open redirect, token leakage, weak JWKS |
| `saml-target` | `lab/saml-target:2026.04.23` | advanced_web, identity_attacks | unsigned assertions, ACS misconfig, XXE, weak audience |
| `tenant-billing-api` | `lab/tenant-billing-api:2026.04.23` | saas_exploitation, api_rest | tenant boundary bypass, horizontal privesc, invitation flow |

### D. CI/CD / supply chain (5 stacks)

| Stack | Imagen/pin | CVE | Chains |
|---|---|---|---|
| `jenkins-old` | `lab/jenkins-cve1000861:2026.04.23` | CVE-2018-1000861 + script console | cicd_supply_chain, bug_bounty |
| `gitlab-ce-old` | `lab/gitlab-ce-cve22205:2026.04.23` | CVE-2021-22205 | cicd_supply_chain, bug_bounty, advanced_web |
| `nexus-old` | `lab/nexus-cve10199:2026.04.23` | CVE-2020-10199 | cicd_supply_chain, cloud_infrastructure |
| `sonarqube-old` | `lab/sonar-cve27986:2026.04.23` | CVE-2020-27986 | cicd_supply_chain, source-audit |
| `gitea-secrets` | `gitea/gitea@sha256:...` | misconfig | cicd_supply_chain |

### E. Data stores expuestos (4 stacks)

| Stack | Imagen | Misconfig |
|---|---|---|
| `mongo-open` | `mongo:6.0.14` | no auth, PII sample |
| `redis-open` | `redis:7.2.4` | unauth, CONFIG abuse |
| `elastic-open` | `elasticsearch:8.12.2` | no auth/TLS, index enum |
| `postgres-open` | `postgres:16.2` | trust auth, dangerous extensions |

### F. Cloud sim (4 stacks)

| Stack | Imagen | Ground truth |
|---|---|---|
| `localstack` | `localstack/localstack:latest` (pinned) | IAM abuse, public buckets, SSRF-to-metadata, lambda env leaks |
| `minio-open` | `minio/minio:RELEASE.2025-07-23T15-54-02Z` | public buckets, leaked keys, object enum |
| `vault-dev-bad` | `hashicorp/vault:1.16.3` | dev mode, root token leak, secret engine misconfig |
| `metadata-sim` | `lab/imds-sim:2026.04.23` | SSRF-to-metadata, short-lived creds |

### G. AD / K8s (2 stacks)

| Stack | Imagen | Notas |
|---|---|---|
| `ad-budget` | `lab/samba-ad-weak:2026.04.23` | LDAP anon/bind, SMB shares, weak pw policy |
| `k3s` + `kube-goat` | `rancher/k3s:latest` host + `lab/kube-goat:2026.04.23` | dashboard/service exposure, permissive RBAC, weak secrets, pod escape |

GOAD-full opt-in (`--profile goad-full`). Default: `ad-budget` Linux/Samba.

### H. Mail (3 stacks)

| Stack | Imagen |
|---|---|
| `mail-weak` | `lab/postfix-dovecot-weak:2026.04.23` |
| `mailhog` | `mailhog/mailhog:v1.0.1` |
| `exchange-mock` | `lab/exchange-mock:2026.04.23` |

### I. IoT / AI / mobile / wireless / VoIP / SCADA (7 stacks)

| Stack | Imagen | Chain |
|---|---|---|
| `iotgoat` | `lab/iotgoat-qemu:2026.04.23` | iot_embedded |
| `promptme` | `lab/promptme:2026.04.23` | ai_ml_attacks |
| `dvaia` | `lab/damn-vulnerable-ai-agent:2026.04.23` | ai_ml_attacks, saas_exploitation |
| `mobile-backend` | `lab/mobile-backend-weak:2026.04.23` | mobile_pentest, api_rest |
| `wireless-sim` | `lab/wireless-sim:2026.04.23` | wireless_pentest |
| `asterisk-weak` | `lab/asterisk-weak:2026.04.23` | voip_scada |
| `openplc-hmi` | `lab/openplc-hmi:2026.04.23` | voip_scada |

## Cobertura por chain

```
generic_web           → WP, Drupal, Joomla, DVWA, bWAPP, WebGoat, Mutillidae
api_rest              → VAmPI, crAPI, mobile-backend, tenant-billing-api
api_graphql           → DVGA
wordpress             → wordpress-cve
django                → django-goat
rails                 → railsgoat
spring                → spring-petclinic-vuln
node                  → juice-shop
php                   → DVWA, bWAPP, Mutillidae, Joomla, WP
go                    → grpc-goat, go-fuzz-svc, VAmPI
dotnet                → dotnet-goat
juice_shop            → juice-shop
exchange              → exchange-mock
mail_server           → mail-weak, mailhog
active_directory      → ad-budget
cloud_infrastructure  → LocalStack, MinIO, Vault, DBs, k3s
cicd_supply_chain     → Jenkins, GitLab, Nexus, Sonar, Gitea
zero_day_research     → go-fuzz-svc, spring, grpc-goat
iot_embedded          → iotgoat
bug_bounty            → todos los subdominios públicos
mobile_pentest        → mobile-backend, VAmPI, crAPI, oauth-lab
wireless_pentest      → wireless-sim
saas_exploitation     → Keycloak, oauth-lab, tenant-billing, crAPI, dvaia
ai_ml_attacks         → promptme, dvaia
voip_scada            → asterisk-weak, openplc-hmi
advanced_web          → Juice Shop, WebGoat, crAPI, Spring, DVGA
identity_attacks      → Keycloak, SAML, OAuth, AD, exchange-mock
container_kubernetes  → k3s, kube-goat
```

28 chains cubiertas, cada una con ≥ 1 stack ejerciéndola.

## CI/CD seeded repos (chain enabler)

Sin repos reales, `/supply-chain` no tiene qué clonar. Sin fixture tokens apuntando a servicios lab, la chain `/supply-chain` → `/cloud-audit` (credencial leaked → MinIO access) es inválida.

### Estructura `targets/seed-repos/`

```
targets/seed-repos/
├── dev-platform/               → Gitea org 'platform'
│   ├── .env.production.bak     → MinIO root key + access-key a finance-private bucket
│   ├── terraform/main.tf       → referencia Vault dev root token
│   ├── .gitlab-ci.yml          → echo pipeline secret (GitLab runner token)
│   └── README.md
├── api-services/               → GitLab project 'backend/api-services'
│   ├── config/database.yml     → postgres-open creds (trust auth target)
│   ├── src/auth/keys.json      → Keycloak weak client secret
│   └── Dockerfile
└── jenkins-jobs/               → Jenkins XML config import
    ├── jobs/deploy-prod/config.xml  → stored creds → minio-open
    └── init.groovy.d/seed-secrets.groovy
```

### Seed flow (Ansible role `seed-cicd-repos`)

1. Post-`docker compose up`, espera GitLab/Gitea/Jenkins ready.
2. `curl -X POST` admin API cada uno: create org, create repo, push seed tree vía `git push`.
3. Jenkins: `curl -X POST /scriptApprovals/approve` + job config XML vía CLI jar.
4. Healthcheck: Ansible espera `/api/v4/projects/backend%2Fapi-services` → 200.

### Chain esperada (medida en postmortem)

```
/supply-chain → clona gitlab-ce-old → encuentra postgres creds en database.yml →
/cloud-audit → conecta postgres-open → dumpa canary rows →
chain-builder → registra cross-stack chain ID en evidence hash-chain
```

Este es el escenario que distingue Leviathan de un scanner plano. Tiene que ser medible. Sin seed repos → imposible.

## Targets propios — Dockerfiles pinneados por commit

Los stacks `lab/*` son builds locales. Cada `targets/<stack>/Dockerfile` usa:

```dockerfile
FROM <base>@sha256:<digest>   # parent pinned by digest, no tag
ENV BUILD_COMMIT=<git-sha>
# ... install vulnerable version ...
```

Lista de Dockerfiles que el scaffold phase materializa (~35 archivos en `targets/`).
