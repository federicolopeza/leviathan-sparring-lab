#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

test -f .env.lab || { echo "[FAIL] .env.lab missing. Copy .env.lab.example -> .env.lab + fill"; exit 1; }
set -a; source .env.lab; set +a

echo "[t+0]   vultr preflight"
make preflight

echo "[t+2]   terraform apply"
make apply

echo "[t+4]   waiting for cloud-init"
SERVER_IP=$(cd terraform && terraform output -raw server_ipv4)
for i in $(seq 1 60); do
  if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i "$SSH_PRIVATE_KEY_PATH" \
       root@"$SERVER_IP" 'test -f /opt/cloud-init-done' 2>/dev/null; then
    echo "[t+$((4+i))] cloud-init done after ${i}s"
    break
  fi
  sleep 5
done

echo "[t+5]   ansible site.yml"
make ansible

echo "[t+22]  docker compose up"
make up

echo "[t+27]  smoke tests (8-check gate)"
make smoke || { echo "[FAIL] smoke gate failed. Benchmark kickoff BLOCKED."; exit 1; }

echo "[t+30]  [OK] Leviathan Sparring Lab deployed. Kickoff permitted."
echo ""
echo "Next: from Leviathan CLI:"
echo "  /pentest https://lab.${BASE_DOMAIN} --roe lab.yaml --mythos stealth --auto-chain 0"
