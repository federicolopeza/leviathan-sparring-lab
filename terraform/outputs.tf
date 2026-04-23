output "server_ipv4" {
  value       = vultr_instance.lab.main_ip
  description = "Public IPv4 -- Ansible + WireGuard bootstrap"
}

output "server_id" {
  value = vultr_instance.lab.id
}

output "server_label" {
  value = vultr_instance.lab.label
}

output "cf_ruleset_id" {
  value = cloudflare_ruleset.lab_allowlist.id
}
