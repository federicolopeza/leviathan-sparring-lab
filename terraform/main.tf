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
  notes             = "Operator SSH bootstrap -- removed after Ansible"
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

# NO inbound 80/443 -- everything arrives via cloudflared outbound QUIC.

# 3. Instance -- ephemeral, no backups, no snapshots
resource "vultr_instance" "lab" {
  label             = var.vultr_instance_label
  plan              = var.vultr_plan
  region            = var.vultr_region
  os_id             = var.vultr_os_id
  ssh_key_ids       = [vultr_ssh_key.bootstrap.id]
  firewall_group_id = vultr_firewall_group.levlab.id

  enable_ipv6      = false
  backups          = "disabled"
  ddos_protection  = false
  activation_email = false
  hostname         = "levlab"

  tags = ["project=levlab", "environment=ephemeral", "destroy_at=24h"]

  # user_data bootstraps vnstat + drops permissive cloud-init firewall
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

# 4. Cloudflare DNS (wildcard + root -> cfargotunnel.com)
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

# 6. Cloudflare ruleset -- custom rule (blocks non-allowlisted IPs)
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
