# 02 — Infrastructure as Code

## Repo structure

```
leviathan-sparring-lab/
├── README.md                   # quickstart
├── vultr-deploy-plan.md        # índice master
├── docs/                       # 00-12 (este dir)
├── .env.lab.example
├── .gitignore
├── Makefile
├── docker-compose.yml          # 28 stacks + observability
├── lab.yaml                    # ROE
├── terraform/
│   ├── providers.tf
│   ├── variables.tf
│   ├── main.tf                 # vultr_instance + vultr_firewall_group + cf DNS
│   ├── outputs.tf
│   └── versions.tf
├── ansible/
│   ├── ansible.cfg
│   ├── inventory.tmpl
│   ├── site.yml
│   ├── roles/
│   │   ├── hardening/
│   │   ├── docker/
│   │   ├── wireguard/
│   │   ├── cloudflared/
│   │   ├── observability/
│   │   ├── zoo-deploy/
│   │   ├── seed-cicd-repos/
│   │   ├── honeytokens/
│   │   └── kill-switch/
│   ├── group_vars/all.yml
│   ├── templates/
│   └── files/
├── ground_truth/
│   └── ground_truth.yml        # 131 entries — ver 05-ground-truth.md
├── scripts/                    # ver 11-operations.md
├── targets/                    # ver 04-zoo-targets.md
└── postmortem-template.md
```

## `.env.lab.example`

```dotenv
# === Cloudflare ===
BASE_DOMAIN=example.com
CF_API_TOKEN=replace_me
CF_ZONE_ID=replace_me
CF_ACCOUNT_ID=replace_me
CF_TUNNEL_ID=replace_me
CF_TUNNEL_TOKEN=replace_me

# === Vultr ===
VULTR_API_KEY=replace_me
VULTR_REGION=ewr              # NYC; LAX=lax, MIA=mia, DFW=dfw
VULTR_PLAN=vhp-8c-16gb-amd    # verify via: vultr-cli plans list
VULTR_OS_ID=2136              # Debian 12 x64 (minimal)
VULTR_INSTANCE_LABEL=levlab-ephemeral

# === Bootstrap SSH (temporary) ===
OPERATOR_PUBLIC_IP=203.0.113.10
SSH_PUBLIC_KEY_PATH=~/.ssh/id_ed25519_vultr_lab.pub
SSH_PRIVATE_KEY_PATH=~/.ssh/id_ed25519_vultr_lab

# === WireGuard ===
WG_SERVER_PRIVATE_KEY=replace_me
WG_SERVER_PUBLIC_KEY=replace_me
WG_CLIENT_PUBLIC_KEY=replace_me
WG_CLIENT_ADDRESS=10.88.0.2/32

# === DNS resolvers (locked egress) ===
DNS_RESOLVER_1=1.1.1.1
DNS_RESOLVER_2=9.9.9.9

# === Observability ===
RUN_ID=20260423-a1
GRAFANA_ADMIN_PASSWORD=replace_me
WAZUH_API_PASSWORD=replace_me
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=replace_me
VAULT_DEV_ROOT_TOKEN_ID=replace_me

# === Bandwidth guard ===
VNSTAT_SOFT_CAP_GB=2000        # warn if projected 24h > 2TB
```

## Terraform — Vultr provider

### `terraform/versions.tf`

```hcl
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    vultr = {
      source  = "vultr/vultr"
      version = "~> 2.21"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
  }
}
```

### `terraform/providers.tf`

```hcl
provider "vultr" {
  api_key     = var.vultr_api_key
  rate_limit  = 700
  retry_limit = 3
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}
```

### `terraform/variables.tf`

```hcl
variable "vultr_api_key"           { type = string, sensitive = true }
variable "cloudflare_api_token"    { type = string, sensitive = true }
variable "cloudflare_zone_id"      { type = string }
variable "cloudflare_account_id"   { type = string }
variable "base_domain"             { type = string }

variable "vultr_region"            { type = string, default = "ewr" }
variable "vultr_plan"              { type = string, default = "vhp-8c-16gb-amd" }
variable "vultr_os_id"             { type = number, default = 2136 }
variable "vultr_instance_label"    { type = string, default = "levlab-ephemeral" }

variable "operator_public_ip"      { type = string }
variable "ssh_public_key"          { type = string }
```

### `terraform/main.tf`

```hcl
# 1. SSH key registered at Vultr
resource "vultr_ssh_key" "bootstrap" {
  name    = "levlab-bootstrap"
  ssh_key = var.ssh_public_key
}

# 2. Firewall group: SSH from operator + WG UDP only
resource "vultr_firewall_group" "levlab" {
  description = "Leviathan Sparring Lab ephemeral firewall"
}

resource "vultr_firewall_rule" "ssh_bootstrap" {
  firewall_group_id = vultr_firewall_group.levlab.id
  protocol          = "tcp"
  ip_type           = "v4"
  subnet            = var.operator_public_ip
  subnet_size       = 32
  port              = "22"
  notes             = "Operator SSH bootstrap — removed after Ansible"
}

resource "vultr_firewall_rule" "wg" {
  firewall_group_id = vultr_firewall_group.levlab.id
  protocol          = "udp"
  ip_type           = "v4"
  subnet            = var.operator_public_ip
  subnet_size       = 32
  port              = "51820"
  notes             = "WireGuard management tunnel"
}

# NO inbound 80/443 — everything arrives via cloudflared outbound QUIC.

# 3. Instance — ephemeral, no backups, no snapshots
resource "vultr_instance" "lab" {
  label             = var.vultr_instance_label
  plan              = var.vultr_plan
  region            = var.vultr_region
  os_id             = var.vultr_os_id
  ssh_key_ids       = [vultr_ssh_key.bootstrap.id]
  firewall_group_id = vultr_firewall_group.levlab.id

  enable_ipv6        = false
  backups            = "disabled"
  ddos_protection    = false
  activation_email   = false
  hostname           = "levlab"

  tags = ["project=levlab", "environment=ephemeral", "destroy_at=24h"]

  # user_data bootstraps vnstat + disables cloud-init permissive firewall
  user_data = base64encode(<<-EOT
    #!/bin/bash
    set -e
    iptables -F INPUT || true
    iptables -P INPUT DROP
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A INPUT -p tcp -s ${var.operator_public_ip}/32 --dport 22 -j ACCEPT
    iptables -A INPUT -p udp -s ${var.operator_public_ip}/32 --dport 51820 -j ACCEPT
    iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    apt-get update -y
    apt-get install -y vnstat
    systemctl enable --now vnstat
    touch /opt/cloud-init-done
  EOT
  )
}

# 4. Cloudflare DNS (wildcard + root → cfargotunnel.com)
resource "cloudflare_dns_record" "lab_root" {
  zone_id = var.cloudflare_zone_id
  name    = "lab"
  type    = "CNAME"
  content = "cfargotunnel.com"
  proxied = true
  ttl     = 1
}

resource "cloudflare_dns_record" "lab_wildcard" {
  zone_id = var.cloudflare_zone_id
  name    = "*.lab"
  type    = "CNAME"
  content = "cfargotunnel.com"
  proxied = true
  ttl     = 1
}

# 5. Cloudflare IP list for runner allowlist
resource "cloudflare_list" "leviathan_runner_ips" {
  account_id  = var.cloudflare_account_id
  name        = "leviathan_runner_ips"
  kind        = "ip"
  description = "Leviathan runner egress IPs for benchmark"
}

# 6. Cloudflare ruleset — custom rule (blocks non-allowlisted IPs)
resource "cloudflare_ruleset" "lab_allowlist" {
  zone_id     = var.cloudflare_zone_id
  name        = "levlab-allowlist"
  description = "Block *.lab.${var.base_domain} if not in runner list"
  kind        = "zone"
  phase       = "http_request_firewall_custom"

  rules {
    action     = "block"
    expression = "http.host contains \".lab.${var.base_domain}\" and not ip.src in $leviathan_runner_ips"
    enabled    = true
  }
}
```

### `terraform/outputs.tf`

```hcl
output "server_ipv4" {
  value       = vultr_instance.lab.main_ip
  description = "Public IPv4 — Ansible + WireGuard bootstrap"
}

output "server_id"       { value = vultr_instance.lab.id }
output "server_label"    { value = vultr_instance.lab.label }
output "cf_ruleset_id"   { value = cloudflare_ruleset.lab_allowlist.id }
```

## Preflight — `scripts/vultr-preflight.sh`

Valida **antes** de `terraform apply`:

1. `vultr-cli account get` — API key válida
2. Plan `vhp-8c-16gb-amd` disponible en región
3. OS ID 2136 = Debian 12 x64
4. Plan disponible en región específica
5. CF_ZONE_ID resuelve a BASE_DOMAIN correcto
6. WG keys presentes (genera si faltan)
7. OPERATOR_PUBLIC_IP auto-detectado si vacío (cloudflare trace)
8. `terraform plan -out=/tmp/levlab.tfplan` dry-run pasa
9. Imprime cost estimate

Código completo en `scripts/vultr-preflight.sh` — ver [11-operations.md](11-operations.md#preflight).

## Ansible — 9 roles en orden

`ansible/site.yml`:

```yaml
- name: Deploy Leviathan Sparring Lab
  hosts: all
  become: true
  roles:
    - hardening          # packages, users, sysctl, auditd, AIDE, AppArmor, fail2ban, CrowdSec, Falco
    - docker             # daemon.json, userns-remap, seccomp, rootless control-plane
    - wireguard          # wg0 + sshd bind to 10.88.0.1
    - cloudflared        # systemd unit + tunnel credentials
    - observability      # Wazuh, Loki, Grafana, Suricata, Arkime, tcpdump ring
    - zoo-deploy         # docker compose up 28 stacks
    - seed-cicd-repos    # Gitea/GitLab/Jenkins fixture repos + tokens
    - honeytokens        # canary files + DB rows + buckets + secrets
    - kill-switch        # Traefik static route + file marker + smoke validation
```

**Doctrina:** `ansible-playbook --check --diff` antes de `--apply`. Idempotente (no shell sin `creates:` o `changed_when:`).

Cada role documentado en:
- hardening → [03-hardening.md](03-hardening.md)
- docker → [03-hardening.md](03-hardening.md#docker-hardening)
- zoo-deploy → [04-zoo-targets.md](04-zoo-targets.md)
- seed-cicd-repos → [04-zoo-targets.md](04-zoo-targets.md#cicd-seeded-repos)
- honeytokens → [06-observability.md](06-observability.md#honeytokens)
- kill-switch → [03-hardening.md](03-hardening.md#kill-switch)
- observability → [06-observability.md](06-observability.md)

## Makefile

```make
SHELL := /bin/bash
include .env.lab
export

TF_DIR=terraform
ANSIBLE_DIR=ansible

.PHONY: preflight init apply ansible up smoke down destroy kill full teardown

preflight:
	@./scripts/vultr-preflight.sh

init: preflight
	cd $(TF_DIR) && terraform init -upgrade

apply:
	cd $(TF_DIR) && terraform apply /tmp/levlab.tfplan

ansible:
	@SERVER_IP=$$(cd $(TF_DIR) && terraform output -raw server_ipv4); \
	echo "lab ansible_host=$$SERVER_IP ansible_user=root" > $(ANSIBLE_DIR)/inventory.ini; \
	ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i $(ANSIBLE_DIR)/inventory.ini \
	  --private-key $$SSH_PRIVATE_KEY_PATH \
	  $(ANSIBLE_DIR)/site.yml

up:
	@SERVER_IP=$$(cd $(TF_DIR) && terraform output -raw server_ipv4); \
	scp -i $$SSH_PRIVATE_KEY_PATH -o StrictHostKeyChecking=no .env.lab root@$$SERVER_IP:/opt/levlab/.env.lab; \
	ssh -i $$SSH_PRIVATE_KEY_PATH -o StrictHostKeyChecking=no root@$$SERVER_IP \
	  'cd /opt/levlab && docker compose --env-file .env.lab up -d'

smoke:
	@./scripts/smoke.sh

down:
	@SERVER_IP=$$(cd $(TF_DIR) && terraform output -raw server_ipv4); \
	ssh -o StrictHostKeyChecking=no root@$$SERVER_IP \
	  'cd /opt/levlab && docker compose down -v --remove-orphans || true'

destroy:
	cd $(TF_DIR) && terraform destroy -auto-approve \
	  -var "vultr_api_key=$$VULTR_API_KEY" \
	  -var "cloudflare_api_token=$$CF_API_TOKEN" \
	  -var "cloudflare_zone_id=$$CF_ZONE_ID" \
	  -var "cloudflare_account_id=$$CF_ACCOUNT_ID" \
	  -var "base_domain=$$BASE_DOMAIN" \
	  -var "operator_public_ip=$$OPERATOR_PUBLIC_IP" \
	  -var "ssh_public_key=$$(cat $$SSH_PUBLIC_KEY_PATH)"

kill:
	@./scripts/kill.sh

full: init apply ansible up smoke
	@echo "[OK] Leviathan Sparring Lab deployed end-to-end. Kickoff permitted."

teardown:
	@./scripts/teardown.sh
```

## Timing targets

| Fase | Budget | Notas |
|---|---:|---|
| Preflight (vultr-cli + tf plan) | 30-60 s | |
| `terraform apply` (Vultr) | 2-3 min | Instance provision ~90s, CF records <10s |
| cloud-init wait | 60-120 s | Debian 12 minimal |
| Ansible full run | 10-18 min | Docker pulls dominan |
| Image builds (`targets/lab/*`) | 8-15 min | Paralelo, concurrente con pulls |
| `docker compose up` | 3-5 min | 28 stacks + obs |
| Smoke gate | 30-60 s | |
| **Total bootstrap** | **< 30 min** | |
| Export artifacts (rsync + hash) | 1-2 min | ≤ 500 MB típico |
| `docker compose down` | 30-60 s | |
| `terraform destroy` (Vultr + CF) | 1-2 min | |
| **Total teardown** | **< 5 min** | |

## Cost

$3.43 compute ($0.143/h × 24h) + ≤$0.60 bandwidth + $0 Cloudflare = **< $5 USD infra**.

Detalle en [12-checklists.md](12-checklists.md#cost-projection).
