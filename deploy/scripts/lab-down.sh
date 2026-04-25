#!/usr/bin/env bash
# lab-down.sh — snapshot + destroy VPS lifecycle (Vultr ephemeral pattern)
#
# Vultr cobra apagado. Solo destroy corta cobro.
# Flow:
#   1. Export artifacts (engagements/, hash-chain verify)
#   2. compose down on VPS
#   3. Vultr API: snapshot create
#   4. Wait snapshot complete
#   5. Vultr API: instance delete
#   6. Update .env.lab clearing VULTR_VPS_IP
#
# Result: VPS gone, snapshot retained for next lab-up restore.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

[[ -f .env.lab ]] || { echo "[FAIL] .env.lab missing"; exit 1; }
set -a; source .env.lab; set +a

: "${VULTR_API_KEY:?missing VULTR_API_KEY}"
: "${VULTR_VPS_IP:?missing VULTR_VPS_IP — nothing to tear down}"
: "${SSH_PRIVATE_KEY_PATH:?missing SSH_PRIVATE_KEY_PATH}"

SSH_USER="${SSH_USER_HARDENED:-levop}"
SSH_PORT="${SSH_PORT:-49222}"
SSH_OPTS="-i $SSH_PRIVATE_KEY_PATH -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -p $SSH_PORT"

log() { echo "[$(date -u +%H:%M:%S)] $*"; }
api() {
    curl -s -H "Authorization: Bearer $VULTR_API_KEY" \
         -H "Content-Type: application/json" \
         "$@"
}

# ─── 1. Export artifacts ───────────────────────────────────────────────
log "[1/6] Export artifacts (hash-chain gated)"
if [[ -x ./scripts/export-artifacts.sh ]]; then
    bash ./scripts/export-artifacts.sh || log "[WARN] export-artifacts had issues"
else
    log "[SKIP] no export-artifacts.sh found"
fi

# ─── 2. Compose down ───────────────────────────────────────────────────
log "[2/6] docker compose down on VPS"
ssh $SSH_OPTS "$SSH_USER@$VULTR_VPS_IP" \
    "cd /opt/levlab && sudo docker compose -f docker-compose.lean.yml down" \
    || log "[WARN] compose down failed (may be already down)"

# ─── 3. Find Vultr instance ID ─────────────────────────────────────────
log "[3/6] Locate Vultr instance by IP"
INSTANCE_ID=$(api https://api.vultr.com/v2/instances \
    | jq -r --arg ip "$VULTR_VPS_IP" '.instances[] | select(.main_ip==$ip) | .id')

[[ -n "$INSTANCE_ID" && "$INSTANCE_ID" != "null" ]] \
    || { log "[FAIL] no Vultr instance with IP $VULTR_VPS_IP"; exit 1; }
log "       instance: $INSTANCE_ID"

# ─── 4. Snapshot ───────────────────────────────────────────────────────
SNAPSHOT_DESC="levlab-auto-$(date -u +%Y%m%d-%H%M)"
log "[4/6] Create snapshot: $SNAPSHOT_DESC"
SNAPSHOT_ID=$(api -X POST https://api.vultr.com/v2/snapshots \
    -d "{\"instance_id\":\"$INSTANCE_ID\",\"description\":\"$SNAPSHOT_DESC\"}" \
    | jq -r '.snapshot.id')

[[ -n "$SNAPSHOT_ID" && "$SNAPSHOT_ID" != "null" ]] \
    || { log "[FAIL] snapshot create failed"; exit 1; }
log "       snapshot: $SNAPSHOT_ID"

# Wait complete
log "       waiting for snapshot to complete (may take 5-15min)..."
for i in $(seq 1 60); do
    STATUS=$(api "https://api.vultr.com/v2/snapshots/$SNAPSHOT_ID" | jq -r '.snapshot.status')
    if [[ "$STATUS" == "complete" ]]; then
        log "       snapshot complete after ${i}0s"
        break
    fi
    if [[ "$STATUS" == "failed" ]]; then
        log "[FAIL] snapshot failed"
        exit 1
    fi
    sleep 30
done

# ─── 5. Destroy instance ───────────────────────────────────────────────
log "[5/6] Destroy instance $INSTANCE_ID"
read -p "Confirm destroy [yes/no]: " -r CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    log "[ABORT] user did not confirm. Snapshot retained: $SNAPSHOT_ID"
    exit 0
fi
api -X DELETE "https://api.vultr.com/v2/instances/$INSTANCE_ID"
log "       instance deletion requested"

# Verify gone
sleep 10
GONE=$(api "https://api.vultr.com/v2/instances/$INSTANCE_ID" | jq -r '.error // empty')
if [[ -n "$GONE" ]]; then
    log "       confirmed gone"
else
    log "[WARN] instance still listed — may be settling, recheck Vultr UI"
fi

# ─── 6. Update .env.lab ────────────────────────────────────────────────
log "[6/6] Clear VULTR_VPS_IP from .env.lab + record snapshot"
sed -i.bak "s/^VULTR_VPS_IP=.*/VULTR_VPS_IP=/" .env.lab
sed -i "s/^LAST_SNAPSHOT_ID=.*/LAST_SNAPSHOT_ID=$SNAPSHOT_ID/" .env.lab \
    || echo "LAST_SNAPSHOT_ID=$SNAPSHOT_ID" >> .env.lab

log ""
log "[OK] Lab down. Snapshot retained: $SNAPSHOT_ID"
log "  - Restore: deploy new VPS from snapshot $SNAPSHOT_ID + lab-up.sh"
log "  - Or delete snapshot to stop storage cost: api -X DELETE /v2/snapshots/$SNAPSHOT_ID"
