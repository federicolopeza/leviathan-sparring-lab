#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source .env.lab

SERVER_IP="$(cd terraform && terraform output -raw server_ipv4)"
ssh -i "$SSH_PRIVATE_KEY_PATH" -o StrictHostKeyChecking=no leviathan@10.88.0.1 \
  'sudo touch /opt/levlab/KILL_SWITCH && \
   sudo docker compose -f /opt/levlab/docker-compose.yml exec traefik touch /logs/kill-active 2>/dev/null || true'
echo "[KILL] marker set. Pipeline aborts on next tool_result."
echo "[*] To resume:"
echo "  ssh leviathan@10.88.0.1 'sudo rm /opt/levlab/KILL_SWITCH'"
