# Leviathan Sparring Lab -- Terraform variables (CF-only flow)
#
# Vultr VPS is created manually via UI by operator. Its public IP lives
# in .env.lab as VULTR_VPS_IP and is consumed by Ansible + scripts.

variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}

variable "cloudflare_zone_id" {
  type = string
}

variable "cloudflare_account_id" {
  type = string
}

variable "base_domain" {
  type        = string
  description = "Parent domain (e.g. melispy.com)"
}
