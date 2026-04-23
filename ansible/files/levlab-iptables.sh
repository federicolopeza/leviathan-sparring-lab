#!/usr/bin/env bash
# Leviathan Sparring Lab — iptables DOCKER-USER + INPUT supplemental rules
# Applied after Docker starts; nftables handles main enforcement.
# This script manages the DOCKER-USER chain that Docker creates.

set -euo pipefail

# Flush DOCKER-USER to start clean (Docker recreates it on restart)
iptables -F DOCKER-USER 2>/dev/null || true

# DOCKER-USER: block public internet access to Docker container networks
# Allow established/related
iptables -I DOCKER-USER -m conntrack --ctstate RELATED,ESTABLISHED -j RETURN

# Allow from WireGuard operator tunnel
iptables -I DOCKER-USER -i wg0 -j RETURN

# Allow localhost
iptables -I DOCKER-USER -s 127.0.0.0/8 -j RETURN

# Allow Docker bridge to bridge (intra-network)
iptables -I DOCKER-USER -s 172.31.0.0/16 -d 172.31.0.0/16 -j RETURN

# Drop everything else targeting Docker bridges
iptables -A DOCKER-USER -d 172.31.0.0/16 -j DROP

# Finalise DOCKER-USER chain
iptables -A DOCKER-USER -j RETURN

# INPUT chain supplemental rules (complement nftables)
# Already handled by nftables; these are idempotent guards

echo "[OK] iptables DOCKER-USER rules applied"
