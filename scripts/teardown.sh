#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

test -f .env.lab || { echo ".env.lab missing"; exit 1; }
set -a; source .env.lab; set +a

echo "[*] Exporting artifacts (hash-chain gated)..."
./scripts/export-artifacts.sh

echo "[*] docker compose down..."
make down || true

echo "[*] terraform destroy..."
make destroy

echo "[*] Verify Vultr resources = 0..."
vultr-cli instance list --output json \
  | jq -e --arg lbl "$VULTR_INSTANCE_LABEL" '[.instances[] | select(.label==$lbl)] | length == 0' \
  || { echo "[FAIL] Vultr instance still present. Manual cleanup needed."; exit 1; }

echo "[*] Cloudflare DNS cleanup verify..."
curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records?name=lab.$BASE_DOMAIN" \
  | jq -e '.result | length == 0' \
  || { echo "[WARN] DNS records remain -- manual cleanup"; }

echo "[*] Cloudflare Tunnel revoke..."
cloudflared tunnel delete "$CF_TUNNEL_ID" --force || true

echo "[*] WireGuard key rotation..."
./scripts/generate-wg-keys.sh --rotate

echo "[OK] Teardown complete. Resources=0. Ready for next ephemeral session."
