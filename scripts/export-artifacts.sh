#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source .env.lab

SERVER_IP="$(cd terraform && terraform output -raw server_ipv4)"
DEST="artifacts/${RUN_ID}"
mkdir -p "$DEST"

# 1. rsync evidence via wg0 (NOT public IP)
rsync -avz -e "ssh -i $SSH_PRIVATE_KEY_PATH -o StrictHostKeyChecking=no" \
  leviathan@10.88.0.1:/opt/levlab/artifacts/ "$DEST/"

# 2. Verify hash-chain BEFORE allowing teardown
python3 -m arsenal.core.evidence_recorder verify \
  --engagement-id "$RUN_ID" \
  --dir "$DEST/evidence" \
  || {
    echo "[FAIL] hash-chain integrity broken. Dumping state + aborting teardown."
    ssh -i $SSH_PRIVATE_KEY_PATH -o StrictHostKeyChecking=no root@$SERVER_IP \
      'journalctl --since -24h > /opt/levlab/artifacts/defensive/journalctl-full.log; \
       docker compose -f /opt/levlab/docker-compose.yml logs > /opt/levlab/artifacts/defensive/compose.log'
    rsync -avz -e "ssh -i $SSH_PRIVATE_KEY_PATH -o StrictHostKeyChecking=no" \
      leviathan@10.88.0.1:/opt/levlab/artifacts/defensive/ "$DEST/defensive/"
    exit 1
  }

# 3. Checksums
sha256sum "$DEST/findings.json" > "$DEST/findings.json.sha256"
sha256sum "$DEST/scoreboard.csv" > "$DEST/scoreboard.csv.sha256"
find "$DEST/evidence" -type f -exec sha256sum {} \; > "$DEST/evidence/MANIFEST.sha256"

echo "[OK] Artifacts exported + hash-chain verified: $DEST"
