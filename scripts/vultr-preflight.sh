#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source .env.lab

echo "[*] Vultr preflight..."

# 1. API key valid
vultr-cli account get >/dev/null || { echo "[FAIL] Vultr API key rejected"; exit 1; }

# 2. Plan available
plan_avail=$(vultr-cli plans list | awk -v plan="$VULTR_PLAN" '$1==plan{print $1}')
if [[ -z "$plan_avail" ]]; then
  echo "[FAIL] Plan $VULTR_PLAN not available. Alternatives:"
  vultr-cli plans list | grep -i '8c' | head -5
  exit 1
fi

# 3. OS ID = Debian 12
os_check=$(vultr-cli os list | awk -v id="$VULTR_OS_ID" '$1==id{print $2}')
[[ "$os_check" == "Debian" ]] || { echo "[FAIL] OS ID $VULTR_OS_ID not Debian (got: $os_check)"; exit 1; }

# 4. Region has plan
region_avail=$(vultr-cli plans list --region "$VULTR_REGION" | grep "$VULTR_PLAN" || true)
[[ -n "$region_avail" ]] || { echo "[FAIL] Plan $VULTR_PLAN not in region $VULTR_REGION"; exit 1; }

# 5. CF zone matches BASE_DOMAIN
cf_zone=$(curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID" | jq -r '.result.name')
[[ "$cf_zone" == "$BASE_DOMAIN" ]] || {
  echo "[FAIL] CF_ZONE_ID $CF_ZONE_ID resolves to '$cf_zone', expected '$BASE_DOMAIN'"
  exit 1
}

# 6. WG keys present or generate
if [[ -z "${WG_SERVER_PRIVATE_KEY:-}" ]]; then
  echo "[*] Generating WG server keypair..."
  ./scripts/generate-wg-keys.sh
fi

# 7. Auto-detect operator IP if empty
if [[ -z "${OPERATOR_PUBLIC_IP:-}" ]]; then
  OPERATOR_PUBLIC_IP=$(curl -s https://cloudflare.com/cdn-cgi/trace | awk -F= '/^ip=/{print $2}')
  echo "[*] Auto-detected OPERATOR_PUBLIC_IP=$OPERATOR_PUBLIC_IP"
  sed -i "s/^OPERATOR_PUBLIC_IP=.*/OPERATOR_PUBLIC_IP=$OPERATOR_PUBLIC_IP/" .env.lab
fi

# 8. terraform plan dry-run
cd terraform
terraform init -upgrade -input=false
terraform plan -out=/tmp/levlab.tfplan \
  -var "vultr_api_key=$VULTR_API_KEY" \
  -var "cloudflare_api_token=$CF_API_TOKEN" \
  -var "cloudflare_zone_id=$CF_ZONE_ID" \
  -var "cloudflare_account_id=$CF_ACCOUNT_ID" \
  -var "base_domain=$BASE_DOMAIN" \
  -var "vultr_region=$VULTR_REGION" \
  -var "vultr_plan=$VULTR_PLAN" \
  -var "vultr_os_id=$VULTR_OS_ID" \
  -var "operator_public_ip=$OPERATOR_PUBLIC_IP" \
  -var "ssh_public_key=$(cat $SSH_PUBLIC_KEY_PATH)" >/dev/null

echo "[OK] Preflight passed. terraform plan saved to /tmp/levlab.tfplan"
echo "[*] Estimated cost: \$$(echo "scale=2; 0.143 * 24" | bc) compute + <=\$0.60 bandwidth"
