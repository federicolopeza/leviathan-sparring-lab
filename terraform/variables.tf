variable "vultr_api_key" {
  type      = string
  sensitive = true
}

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
  type = string
}

variable "vultr_region" {
  type    = string
  default = "ewr"
}

variable "vultr_plan" {
  type    = string
  default = "vhp-8c-16gb-amd"
}

variable "vultr_os_id" {
  type    = number
  default = 2136
}

variable "vultr_instance_label" {
  type    = string
  default = "levlab-ephemeral"
}

variable "operator_public_ip" {
  type = string
}

variable "ssh_public_key" {
  type = string
}
