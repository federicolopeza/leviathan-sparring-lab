# Melispy app policy — read-only access to service secrets
# Phase 5 will add per-service sub-paths for isolation
path "secret/data/melispy/*" {
  capabilities = ["read", "list"]
}

path "secret/metadata/melispy/*" {
  capabilities = ["list"]
}
