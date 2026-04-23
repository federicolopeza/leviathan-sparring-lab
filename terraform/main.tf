# Leviathan Sparring Lab -- Terraform (VPS-already-exists flow)
#
# Operator created the Vultr VPS manually via UI. This Terraform
# manages ONLY Cloudflare resources: DNS records + Tunnel.
#
# No vultr_* resources. No CF IP allowlist (benchmark accepts any IP,
# WAF Managed Rules + OWASP CRS still measure attack traffic).

# 1. Cloudflare Tunnel (cloudflared will run on VPS pointing here)
resource "cloudflare_zero_trust_tunnel_cloudflared" "lab" {
  account_id = var.cloudflare_account_id
  name       = "levlab-tunnel"
  config_src = "local"
}

# Expose tunnel token as output so ansible can install cloudflared with it
# Note: with config_src="local" the tunnel config lives in /etc/cloudflared/
# on the VPS, not managed by cloudflare_zero_trust_tunnel_config.

# 2. Cloudflare DNS -- wildcard + root subdomain -> cfargotunnel
resource "cloudflare_dns_record" "lab_root" {
  zone_id = var.cloudflare_zone_id
  name    = "lab"
  type    = "CNAME"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.lab.id}.cfargotunnel.com"
  proxied = true
  ttl     = 1
}

resource "cloudflare_dns_record" "lab_wildcard" {
  zone_id = var.cloudflare_zone_id
  name    = "*.lab"
  type    = "CNAME"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.lab.id}.cfargotunnel.com"
  proxied = true
  ttl     = 1
}
