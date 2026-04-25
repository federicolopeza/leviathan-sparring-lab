#!/usr/bin/env bash
# lab-up.sh — bring up Leviathan Sparring Lab v2 on a fresh Vultr VPS
#
# Prereqs:
#   - VPS already deployed via Vultr UI (manual)
#   - VULTR_VPS_IP set in .env.lab
#   - SSH key matching VPS authorized_keys in $SSH_PRIVATE_KEY_PATH
#   - .env.lab filled (CF_API_TOKEN, CF_TUNNEL_TOKEN, BASE_DOMAIN, etc)
#
# Flow:
#   1. Validate env + SSH reachable
#   2. rsync repo to VPS:/opt/levlab
#   3. Run harden.sh on VPS (idempotent, all phases)
#   4. Generate WG keys (if not present)
#   5. Bring up docker compose lean
#   6. Smoke test
#
# Idempotent: re-run safely.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# ─── Env ────────────────────────────────────────────────────────────────
[[ -f .env.lab ]] || { echo "[FAIL] .env.lab missing. cp .env.lab.example .env.lab + fill"; exit 1; }
set -a; source .env.lab; set +a

: "${VULTR_VPS_IP:?missing VULTR_VPS_IP in .env.lab}"
: "${SSH_PRIVATE_KEY_PATH:?missing SSH_PRIVATE_KEY_PATH in .env.lab}"
: "${BASE_DOMAIN:?missing BASE_DOMAIN}"
: "${CF_API_TOKEN:?missing CF_API_TOKEN}"
: "${CF_TUNNEL_TOKEN:?missing CF_TUNNEL_TOKEN}"

SSH_USER="${SSH_USER:-root}"
SSH_PORT="${SSH_PORT_BOOTSTRAP:-22}"  # initial; switches to 49222 after harden
REMOTE_DIR="/opt/levlab"
SSH_OPTS="-i $SSH_PRIVATE_KEY_PATH -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -p $SSH_PORT"
RSYNC_OPTS="-e \"ssh $SSH_OPTS\" -avz --delete --exclude=.git --exclude=engagements/*/evidence --exclude='*.bak'"

ssh_exec() { ssh $SSH_OPTS "$SSH_USER@$VULTR_VPS_IP" "$@"; }

log() { echo "[$(date -u +%H:%M:%S)] $*"; }

# ─── 1. SSH preflight ──────────────────────────────────────────────────
log "[1/6] SSH preflight to $VULTR_VPS_IP:$SSH_PORT"
if ! ssh_exec "echo OK" >/dev/null 2>&1; then
    log "[FAIL] SSH unreachable. Check Firewall Group + key + IP."
    exit 1
fi
log "       SSH OK"

# ─── 2. Rsync repo ─────────────────────────────────────────────────────
log "[2/6] Rsync repo to $VULTR_VPS_IP:$REMOTE_DIR"
ssh_exec "mkdir -p $REMOTE_DIR && chown -R \$(whoami) $REMOTE_DIR"
eval rsync $RSYNC_OPTS "$ROOT_DIR/" "$SSH_USER@$VULTR_VPS_IP:$REMOTE_DIR/"
log "       rsync done"

# ─── 3. Run harden.sh ──────────────────────────────────────────────────
log "[3/6] Run harden.sh (all phases) on VPS — may take 5-10min"
ssh_exec "cd $REMOTE_DIR && sudo OPERATOR_IP='${OPERATOR_IP:-179.24.190.234}' SSH_USER='${SSH_USER_HARDENED:-levop}' bash scripts/harden.sh --phase=all"
log "       harden.sh done"

# ─── 4. WG peer reminder ───────────────────────────────────────────────
log "[4/6] WireGuard peer setup"
WG_SERVER_PUB=$(ssh_exec "sudo cat /var/lib/levlab-harden/wg-server.pub" 2>/dev/null || echo "")
if [[ -n "$WG_SERVER_PUB" ]]; then
    log "       WG server pubkey: $WG_SERVER_PUB"
    log "       Run on laptop: bash scripts/generate-wg-keys.sh --client"
    log "       Then add client peer to VPS /etc/wireguard/wg0.conf and: sudo systemctl restart wg-quick@wg0"
fi

# ─── 5. Compose up ─────────────────────────────────────────────────────
log "[5/6] docker compose up (lean stack)"
ssh_exec "cd $REMOTE_DIR && sudo docker compose -f docker-compose.lean.yml --env-file .env.lab up -d"
sleep 10
ssh_exec "sudo docker compose -f $REMOTE_DIR/docker-compose.lean.yml ps"

# ─── 6. Smoke test ─────────────────────────────────────────────────────
log "[6/6] Smoke test"
ssh_exec "cd $REMOTE_DIR && bash scripts/smoke.sh" || log "[WARN] smoke test partial (some checks may need WG up)"

log ""
log "[OK] Lab up. Next steps:"
log "  - Add WG peer (see step 4 output)"
log "  - Verify Cloudflare Tunnel: https://gt.${BASE_DOMAIN}"
log "  - Activate first GT: bash scripts/gt-rotate.sh dvwa"
log "  - Lynis audit: ssh $SSH_USER@$VULTR_VPS_IP 'sudo lynis audit system' | grep 'Hardening index'"
log "  - Tighten firewall (close SSH public, only WG): sudo ufw delete allow ..."
