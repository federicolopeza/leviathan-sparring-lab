output "tunnel_id" {
  value       = cloudflare_zero_trust_tunnel_cloudflared.lab.id
  description = "CF tunnel ID -- consumed by cloudflared on VPS"
}

output "tunnel_token" {
  value       = cloudflare_zero_trust_tunnel_cloudflared.lab.tunnel_token
  description = "CF tunnel token -- used by cloudflared service"
  sensitive   = true
}

output "lab_root_fqdn" {
  value = "lab.${var.base_domain}"
}

output "lab_wildcard_fqdn" {
  value = "*.lab.${var.base_domain}"
}
