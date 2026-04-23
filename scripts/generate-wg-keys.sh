#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-generate}"

if [[ "$MODE" == "--rotate" ]]; then
  echo "[*] Rotating WG keys (new server keypair, archiving old)..."
  cp .env.lab ".env.lab.rotated.$(date +%s)"
fi

# Generate new server keypair
WG_SERVER_PRIVATE=$(wg genkey)
WG_SERVER_PUBLIC=$(echo "$WG_SERVER_PRIVATE" | wg pubkey)

# Update .env.lab in place
if [[ -f .env.lab ]]; then
  if grep -q "^WG_SERVER_PRIVATE_KEY=" .env.lab; then
    sed -i "s|^WG_SERVER_PRIVATE_KEY=.*|WG_SERVER_PRIVATE_KEY=$WG_SERVER_PRIVATE|" .env.lab
    sed -i "s|^WG_SERVER_PUBLIC_KEY=.*|WG_SERVER_PUBLIC_KEY=$WG_SERVER_PUBLIC|" .env.lab
  else
    echo "WG_SERVER_PRIVATE_KEY=$WG_SERVER_PRIVATE" >> .env.lab
    echo "WG_SERVER_PUBLIC_KEY=$WG_SERVER_PUBLIC" >> .env.lab
  fi
fi

echo "[OK] WG server keypair generated"
echo "    public: $WG_SERVER_PUBLIC"
echo ""
echo "Operator: add this pubkey to your laptop's wg0 config as [Peer] PublicKey"
