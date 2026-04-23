# 01 — Arquitectura de red

## Topología

```
              ┌───────────── Cloudflare Edge ─────────────┐
              │ DNS + Proxy + WAF + TLS + Managed Rules   │
              │ OWASP CRS PL2 + Custom IP list allowlist  │
              └───────────────────────────────────────────┘
                           │ (outbound tunnel only)
                           │ QUIC 7844 / HTTPS 443
                           │
        ┌──────────────── Vultr VPS (Debian 12 minimal) ────────────────┐
        │ public iface: UDP/51820 (WG bootstrap only)                   │
        │ no public 22 / 80 / 443 after hour 0                          │
        │                                                               │
        │  cloudflared ─► traefik ─► modsec-<stack> ─► app              │
        │                     │                                         │
        │                     ├─ cms_net         ── 7 CMS/appsec stacks│
        │                     ├─ api_net         ── 6 API targets      │
        │                     ├─ id_net          ── 4 identity stacks  │
        │                     ├─ cicd_net        ── 5 CI/CD pins       │
        │                     ├─ data_net        ── 4 DB-open          │
        │                     ├─ cloud_net       ── 4 cloud-sim        │
        │                     ├─ k8s_net         ── k3s + kube-goat    │
        │                     ├─ ot_ai_net       ── AI/LLM + OT        │
        │                     └─ mobile_net      ── mobile backends    │
        │                                                               │
        │  obs_net: Wazuh + Loki + Promtail + Grafana + Prometheus +   │
        │           cAdvisor + Suricata + Falco + Arkime + node_exp    │
        │                                                               │
        │  pivot_net: explicit lateral-movement surface                 │
        └───────────────────────────────────────────────────────────────┘
                           │ wg0 (10.88.0.1/24)
                           │
              ┌── Operator laptop (10.88.0.2) ──┐
              │ SSH + Ansible + Leviathan CLI    │
              └──────────────────────────────────┘
```

## Principios operativos

1. **No 80/443 público.** HTTP(S) entra vía Cloudflare Tunnel → `cloudflared` local → Traefik @ `127.0.0.1:8443`.
2. **Allowlist en Cloudflare edge, no IP Access Allow.** Custom Rule + IP List (`leviathan_runner_ips`). Preserva WAF observability (IP Access Allow saltea Managed Rules → mata el benchmark).
3. **SSH público muere post-bootstrap.** `sshd` escucha solo en `10.88.0.1` (wg0).
4. **Egress lockdown 2-phase.** Bootstrap: DNS/NTP/HTTPS/tunnel. Locked: DNS/NTP/tunnel/wg only.
5. **Bridges Docker por categoría + `pivot_net`** para lateral movement controlado.

## Docker networks

```yaml
edge_net:    172.31.0.0/24     # traefik exposure
obs_net:     172.31.10.0/24    # observability
cms_net:     172.31.20.0/24    # WordPress/Drupal/Joomla/DVWA/WebGoat/Mutillidae/bWAPP
api_net:     172.31.30.0/24    # VAmPI/DVGA/crAPI/gRPC-goat/dotnet-goat/go-fuzz-svc
id_net:      172.31.40.0/24    # Keycloak/OAuth/SAML/tenant-billing
cicd_net:    172.31.50.0/24    # Jenkins/GitLab/Nexus/SonarQube/Gitea
data_net:    172.31.60.0/24    # mongo/redis/postgres/elastic open
cloud_net:   172.31.70.0/24    # LocalStack/MinIO/Vault/metadata-sim
k8s_net:     172.31.80.0/24    # k3s + kube-goat
ot_ai_net:   172.31.90.0/24    # iotgoat/promptme/dvaia/asterisk/openplc
mobile_net:  172.31.100.0/24   # mobile-backend + wireless-sim
pivot_net:   172.31.200.0/24   # cross-category lateral surface
```

## Hostnames (33 total)

```
lab.${BASE_DOMAIN}              landing / kill-switch / smoke
wp.lab                          WordPress CVE pin
drupal.lab                      Drupal CVE pin
joomla.lab                      Joomla CVE pin
juice.lab                       Juice Shop
dvwa.lab                        DVWA
webgoat.lab                     WebGoat
mutillidae.lab                  Mutillidae
bwapp.lab                       bWAPP
django.lab                      DjangoGoat
rails.lab                       RailsGoat
spring.lab                      Spring PetClinic vulnerable
dotnet.lab                      dotnet-goat
gofuzz.lab                      go-fuzz-svc
vampi.lab                       VAmPI
dvga.lab                        DVGA
crapi.lab                       crAPI
grpc.lab                        gRPC-goat gateway
keycloak.lab                    Keycloak weak
oauth.lab                       OAuth lab
saml.lab                        SAML vulnerable SP
tenant-billing.lab              multi-tenant API
jenkins.lab                     Jenkins 2018-1000861
gitlab.lab                      GitLab 22205
nexus.lab                       Nexus 10199
sonar.lab                       SonarQube 27986
gitea.lab                       Gitea w/ seeded secrets
minio.lab                       MinIO w/ finance-private bucket
vault.lab                       Vault dev mode
aws.lab                         LocalStack
k8s.lab                         kube-goat ingress
mail.lab                        postfix/dovecot weak
exchange.lab                    Exchange mock
iot.lab                         IoTGoat QEMU
ai.lab                          PromptMe / DVAIA
mobile.lab                      mobile-backend
voip.lab                        Asterisk
scada.lab                       OpenPLC HMI
wazuh.lab                       Wazuh dashboard (operator only)
grafana.lab                     Grafana (operator only)
```

Cloudflared publica `*.lab.${BASE_DOMAIN}` + `lab.${BASE_DOMAIN}`, todo al mismo Traefik interno.

## Cloudflare configuración exacta

**NO usar:** `IP Access Rule = Allow`. Saltea Managed Rules + rate limiting + Custom Rules → invalida medición WAF.

**Sí usar:**

- **Managed Ruleset** enabled, acción `log` default, `block` en `/admin`, `/wp-admin`, `/login`, `/api/internal`
- **OWASP Core Ruleset** enabled, Paranoia Level `PL2` baseline
- **Custom IP List** `leviathan_runner_ips` → runner egress IPs
- **Custom Rule** (zone-level):
  ```
  Expression: http.host contains ".lab.${BASE_DOMAIN}" and not ip.src in $leviathan_runner_ips
  Action: block
  ```
- **Payload logging** on para rule IDs que querés validar bypass
- **Logpush** a R2 bucket o endpoint externo para correlación defensiva

Todo esto se provisiona vía Terraform (`cloudflare_list` + `cloudflare_ruleset`) — ver [02-infrastructure.md](02-infrastructure.md).

## Vultr-specific edge cases

| Issue | Mitigación |
|---|---|
| Vultr Debian 12 cloud-init trae `iptables` permisivo | Preflight: `iptables -F INPUT && iptables -P INPUT DROP` antes de Ansible, después `systemctl disable cloud-init` |
| Vultr bandwidth cap 3TB/month | `vnstat` + cron 15min: si proyección 24h > 2TB → escribe `/opt/levlab/BANDWIDTH_WARN` + email operador vía wg0 |
| Snapshots automáticos (costo + data hygiene) | `vultr_instance.lab` con `backups = "disabled"`. Verify post-apply |
| Metadata leak vía SSRF-to-`169.254.169.254` | nftables OUTPUT: `ip daddr 169.254.169.254 drop` aplicada **después** de cloud-init (sino rompe) |
| Vultr API key scope | Sub-account API key scoped al tag `project=levlab` — destroy no afecta otros proyectos |

## Por qué Vultr

- `vhp-8c-16gb-amd` ($0.143/h) → $3.43 para 24h
- AMD EPYC cores mejor que Intel `vc2` para Docker paralelo
- Vultr NYC/LAX con PoP Cloudflare cercano (< 5ms tunnel latency)
- Billing por hora, sin commitment
- API + Terraform provider maduro (`vultr/vultr ~>2.21`)

## Por qué control plane rootless + target plane rootful

Rootless total rompe Suricata/Arkime/pcap/DOCKER-USER (pierden visibilidad bridge).

- **Control plane rootless** (build tools, CLI operador)
- **Target plane rootful + `userns-remap` + seccomp + AppArmor + `cap_drop` + `no-new-privileges`**

Preserva telemetría sin abandonar hardening. Ver [03-hardening.md](03-hardening.md#docker-hardening).

## WireGuard + SSH

```ini
# /etc/wireguard/wg0.conf
[Interface]
Address = 10.88.0.1/24
ListenPort = 51820
PrivateKey = ${WG_SERVER_PRIVATE_KEY}

[Peer]
PublicKey = ${WG_CLIENT_PUBLIC_KEY}
AllowedIPs = 10.88.0.2/32
PersistentKeepalive = 25
```

SSH config:
```
Port 22
ListenAddress 10.88.0.1
PermitRootLogin no
PasswordAuthentication no
AllowUsers leviathan
```

Server keypair lo genera `scripts/generate-wg-keys.sh`. Operador provee pubkey only.
