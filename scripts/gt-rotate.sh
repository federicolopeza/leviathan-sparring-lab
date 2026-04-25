#!/usr/bin/env bash
# gt-rotate.sh — swap the active Ground Truth target
#
# Usage:
#   ./scripts/gt-rotate.sh <stack-name>          # rotate to <stack-name>
#   ./scripts/gt-rotate.sh --list                # list available stacks
#   ./scripts/gt-rotate.sh --status              # show current active GT
#
# Reads metadata from targets/catalog.yml.
# Updates GT_IMAGE + GT_PORT in .env.lab and bounces the gt-active container.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CATALOG="targets/catalog.yml"
ENV_FILE=".env.lab"
COMPOSE_FILE="docker-compose.lean.yml"

[[ -f "$CATALOG" ]] || { echo "[FAIL] $CATALOG missing"; exit 1; }
[[ -f "$ENV_FILE" ]] || { echo "[FAIL] $ENV_FILE missing"; exit 1; }
command -v yq >/dev/null || { echo "[FAIL] install yq: https://github.com/mikefarah/yq"; exit 1; }

case "${1:-}" in
    --list)
        echo "Available targets (catalog):"
        yq '.targets[].name' "$CATALOG" | sort
        exit 0
        ;;
    --status)
        echo "Current GT_ACTIVE: $(grep ^GT_ACTIVE= "$ENV_FILE" | cut -d= -f2)"
        echo "Current GT_IMAGE:  $(grep ^GT_IMAGE= "$ENV_FILE" | cut -d= -f2)"
        exit 0
        ;;
    "" | -h | --help)
        echo "Usage: $0 <stack-name> | --list | --status"
        exit 0
        ;;
esac

STACK="$1"

# Lookup in catalog
META=$(yq ".targets[] | select(.name == \"$STACK\")" "$CATALOG")
[[ -n "$META" ]] || { echo "[FAIL] stack '$STACK' not in catalog. Run: $0 --list"; exit 1; }

IMAGE=$(echo "$META" | yq '.image')
PORT=$(echo "$META" | yq '.port // 80')
NETWORK=$(echo "$META" | yq '.network // "target_net"')
DESCRIPTION=$(echo "$META" | yq '.description')

echo "[*] Rotating to: $STACK"
echo "    image:       $IMAGE"
echo "    port:        $PORT"
echo "    network:     $NETWORK"
echo "    description: $DESCRIPTION"

# Update .env.lab
update_env() {
    local key="$1"
    local val="$2"
    if grep -q "^$key=" "$ENV_FILE"; then
        sed -i.bak "s|^$key=.*|$key=$val|" "$ENV_FILE"
    else
        echo "$key=$val" >> "$ENV_FILE"
    fi
}
update_env GT_ACTIVE "$STACK"
update_env GT_IMAGE "$IMAGE"
update_env GT_PORT "$PORT"

# Bounce gt-active container
echo "[*] Bouncing gt-active container..."
if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps gt-active >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop gt-active || true
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" rm -f gt-active || true
fi
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull gt-active || true
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d gt-active

echo ""
echo "[OK] GT rotated to $STACK"
echo "     URL: https://gt.\${BASE_DOMAIN}"
echo "     Verify: docker compose -f $COMPOSE_FILE logs -f gt-active"
