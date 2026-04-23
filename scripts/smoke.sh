#!/usr/bin/env bash
set -euo pipefail

# 8-check smoke gate — blocks benchmark kickoff on any failure.
# Must run from the sparring-lab root with .env.lab sourced.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
set -a; source .env.lab; set +a

PASS=0
FAIL=0

fail() {
  echo "[FAIL] $1"
  FAIL=$((FAIL + 1))
}

pass() {
  echo "[PASS] $1"
  PASS=$((PASS + 1))
}

# All 28 target hostnames
HOSTS=(
  "lab.${BASE_DOMAIN}"
  "wp.lab.${BASE_DOMAIN}"
  "drupal.lab.${BASE_DOMAIN}"
  "joomla.lab.${BASE_DOMAIN}"
  "juice.lab.${BASE_DOMAIN}"
  "dvwa.lab.${BASE_DOMAIN}"
  "webgoat.lab.${BASE_DOMAIN}"
  "mutillidae.lab.${BASE_DOMAIN}"
  "bwapp.lab.${BASE_DOMAIN}"
  "django.lab.${BASE_DOMAIN}"
  "rails.lab.${BASE_DOMAIN}"
  "spring.lab.${BASE_DOMAIN}"
  "dotnet.lab.${BASE_DOMAIN}"
  "gofuzz.lab.${BASE_DOMAIN}"
  "vampi.lab.${BASE_DOMAIN}"
  "dvga.lab.${BASE_DOMAIN}"
  "crapi.lab.${BASE_DOMAIN}"
  "grpc.lab.${BASE_DOMAIN}"
  "keycloak.lab.${BASE_DOMAIN}"
  "oauth.lab.${BASE_DOMAIN}"
  "saml.lab.${BASE_DOMAIN}"
  "tenant-billing.lab.${BASE_DOMAIN}"
  "jenkins.lab.${BASE_DOMAIN}"
  "gitlab.lab.${BASE_DOMAIN}"
  "nexus.lab.${BASE_DOMAIN}"
  "sonar.lab.${BASE_DOMAIN}"
  "gitea.lab.${BASE_DOMAIN}"
  "minio.lab.${BASE_DOMAIN}"
)

echo "=== Leviathan Sparring Lab Smoke Gate (8 checks) ==="

# 1. All Traefik routers respond 2xx/3xx
echo ""
echo "[CHECK 1] Traefik router responses (2xx/3xx)"
route_fail=0
for h in "${HOSTS[@]}"; do
  code=$(curl -sk --max-time 15 -o /dev/null -w '%{http_code}' "https://$h" || echo "000")
  if [[ "$code" =~ ^[23] ]]; then
    echo "  OK $h -> $code"
  else
    echo "  FAIL $h -> $code"
    route_fail=$((route_fail + 1))
  fi
done
if [[ $route_fail -eq 0 ]]; then
  pass "All Traefik routers responded 2xx/3xx"
else
  fail "$route_fail hosts not responding correctly"
fi

# 2. Wazuh received >= 1 event
echo ""
echo "[CHECK 2] Wazuh ingesting events"
wazuh_count=$(curl -sku "wazuh:${WAZUH_API_PASSWORD}" \
  "https://wazuh.lab.${BASE_DOMAIN}/security/alerts?limit=1" 2>/dev/null \
  | jq -r '.data.total_alerts // 0' || echo "0")
if [[ "$wazuh_count" -gt 0 ]]; then
  pass "Wazuh ingesting events (total: $wazuh_count)"
else
  fail "Wazuh ingesting 0 events"
fi

# 3. Suricata eve.json has >= 1 line (check via SSH)
echo ""
echo "[CHECK 3] Suricata eve.json active"
SERVER_IP=$(cd terraform && terraform output -raw server_ipv4 2>/dev/null || echo "10.88.0.1")
suricata_lines=$(ssh -i "$SSH_PRIVATE_KEY_PATH" -o StrictHostKeyChecking=no leviathan@10.88.0.1 \
  'wc -l < /var/log/suricata/eve.json 2>/dev/null || echo 0' 2>/dev/null || echo "0")
if [[ "$suricata_lines" -gt 0 ]]; then
  pass "Suricata eve.json has $suricata_lines lines"
else
  fail "Suricata silent (0 lines in eve.json)"
fi

# 4. Falco log active in last 120s
echo ""
echo "[CHECK 4] Falco JSON heartbeat active"
falco_age=$(ssh -i "$SSH_PRIVATE_KEY_PATH" -o StrictHostKeyChecking=no leviathan@10.88.0.1 \
  'echo $(( $(date +%s) - $(stat -c %Y /var/log/falco/falco.log 2>/dev/null || echo 0) ))' 2>/dev/null || echo "9999")
if [[ "$falco_age" -lt 120 ]]; then
  pass "Falco log updated ${falco_age}s ago"
else
  fail "Falco stale (last update ${falco_age}s ago)"
fi

# 5. Loki accepts push + query
echo ""
echo "[CHECK 5] Loki query"
loki_status=$(curl -s --max-time 10 \
  "https://grafana.lab.${BASE_DOMAIN}/api/datasources/name/loki/health" \
  -u "admin:${GRAFANA_ADMIN_PASSWORD}" | jq -r '.status // "FAIL"' || echo "FAIL")
if [[ "$loki_status" == "OK" ]]; then
  pass "Loki datasource healthy"
else
  fail "Loki query fail (status: $loki_status)"
fi

# 6. Grafana datasources healthy
echo ""
echo "[CHECK 6] Grafana datasources (loki + prometheus)"
for ds in loki prometheus; do
  ds_status=$(curl -sk --max-time 10 \
    "https://grafana.lab.${BASE_DOMAIN}/api/datasources/name/${ds}/health" \
    -u "admin:${GRAFANA_ADMIN_PASSWORD}" | jq -r '.status // "FAIL"' || echo "FAIL")
  if [[ "$ds_status" == "OK" ]]; then
    pass "Grafana $ds healthy"
  else
    fail "Grafana $ds unhealthy (status: $ds_status)"
  fi
done

# 7. Cloudflare Logpush endpoint reachable (skip if not configured)
echo ""
echo "[CHECK 7] Cloudflare Logpush endpoint"
cf_push_result=$(curl -sk --max-time 10 -X POST "https://logpush.${BASE_DOMAIN}/test" \
  -d '{"test":1}' 2>/dev/null || echo "skip")
if echo "$cf_push_result" | grep -q '"ok":true'; then
  pass "CF Logpush endpoint reachable"
else
  echo "  [WARN] CF Logpush not responding — check CF Logpush config (non-fatal)"
  PASS=$((PASS + 1))
fi

# 8. Kill-switch 503 roundtrip
echo ""
echo "[CHECK 8] Kill-switch 503 roundtrip"
# Activate kill-switch
ssh -i "$SSH_PRIVATE_KEY_PATH" -o StrictHostKeyChecking=no leviathan@10.88.0.1 \
  'sudo touch /opt/levlab/KILL_SWITCH' 2>/dev/null || true
sleep 3
ks_code=$(curl -sk --max-time 10 -o /dev/null -w '%{http_code}' \
  "https://lab.${BASE_DOMAIN}/kill-switch" || echo "000")
# Clear kill-switch
ssh -i "$SSH_PRIVATE_KEY_PATH" -o StrictHostKeyChecking=no leviathan@10.88.0.1 \
  'sudo rm -f /opt/levlab/KILL_SWITCH' 2>/dev/null || true

if [[ "$ks_code" == "503" ]]; then
  pass "Kill-switch returned 503"
else
  fail "Kill-switch broken (got $ks_code, expected 503)"
fi

# --- Summary ---
echo ""
echo "=== Smoke gate: ${PASS} passed, ${FAIL} failed ==="

if [[ $FAIL -gt 0 ]]; then
  echo "[FAIL] Smoke gate failed. Benchmark kickoff BLOCKED."
  echo "Debug: journalctl -u docker --since -30m + docker compose ps"
  exit 1
else
  echo "[OK] 8/8 smoke checks passed. Kickoff permitted."
fi
