terraform {
  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "~> 3.0"
    }
  }
}

# Fixture — deliberate credential leak for lab canary detection
# vault-dev-bad runs in dev mode; this token is the static root token
provider "vault" {
  address = "http://vault-dev-bad:8200"
  token   = "root-dev-token-deliberate"
}

resource "vault_kv_secret_v2" "minio_creds" {
  mount = "secret"
  name  = "minio/finance-private"

  data_json = jsonencode({
    access_key = "AKIAFAKE1234567890AB"
    secret_key = "sFakeSecretKeyForLabCanary1234567890xxxxx"
    bucket     = "finance-private"
  })
}

resource "vault_kv_secret_v2" "gitea_webhook" {
  mount = "secret"
  name  = "gitea"

  data_json = jsonencode({
    admin_token  = "gitea-admin-fixture-token-abc123"
    webhook_key  = "gitea-webhook-secret-fixture-xyz"
    api_endpoint = "http://gitea-secrets:3000"
  })
}
