#!/usr/bin/env bash
# triage.sh — quick attacker overview during engagement
#
# Run on VPS:
#   ssh root@<vps_ip> "bash /opt/levlab/scripts/triage.sh"
#
# Outputs full snapshot of last 1h: honeypot hits, falco alerts, fail2ban bans, top IPs.

set -uo pipefail

WINDOW="${1:-1h}"
RED='\033[0;31m'; YELLOW='\033[0;33m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}═══════════════════════════════════════════════════════"
echo -e " Levlab Triage — last ${WINDOW}"
echo -e "═══════════════════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}🍯 Top honeypot IP sources${NC}"
docker logs --since "$WINDOW" levlab-gt-honeypot 2>&1 \
  | grep WARNING | grep -oE '"src": "[^"]*"' | sort | uniq -c | sort -rn | head -10 \
  || echo "  (none)"

echo -e "\n${YELLOW}🍯 Honeypot categories triggered${NC}"
docker logs --since "$WINDOW" levlab-gt-honeypot 2>&1 \
  | grep WARNING | grep -oE '"category": "[^"]*"' | sort | uniq -c | sort -rn \
  || echo "  (none)"

echo -e "\n${YELLOW}🍯 Critical / High severity events${NC}"
docker logs --since "$WINDOW" levlab-gt-honeypot 2>&1 \
  | grep WARNING | grep -E '"severity": "(critical|high)"' \
  | python3 -c '
import sys, json, re
for l in sys.stdin:
    m = re.search(r"\"msg\":(\{.*\})", l)
    if not m:
        continue
    try:
        d = json.loads(m.group(1))
        sev = d.get("severity")
        src = d.get("src")
        meth = d.get("method")
        host = d.get("host")
        path = d.get("path")
        cat = d.get("category")
        print("  [" + sev + "] " + src + " -> " + meth + " " + host + path + " (" + cat + ")")
    except Exception:
        pass
' | head -20 \
  || echo "  (none)"

echo -e "\n${RED}🚨 Falco alerts (host)${NC}"
journalctl --since "$WINDOW ago" -u falco-modern-bpf.service --no-pager 2>/dev/null \
  | grep -E "Notice|Warning|Critical|Error" | tail -10 \
  || echo "  (none)"

echo -e "\n${RED}🚫 fail2ban bans${NC}"
fail2ban-client status sshd 2>/dev/null | grep -A1 "Banned IP" || echo "  (no bans)"

echo -e "\n${YELLOW}🔐 Top 401/403 sources (auth bruteforce)${NC}"
docker logs --since "$WINDOW" levlab-traefik 2>&1 \
  | grep -E ' 401 | 403 ' | awk '{print $1}' | sort | uniq -c | sort -rn | head -10 \
  || echo "  (none)"

echo -e "\n${YELLOW}🌐 Top hosts hit${NC}"
docker logs --since "$WINDOW" levlab-traefik 2>&1 \
  | grep -oE '"[^"]+\.melispy\.com"' | sort | uniq -c | sort -rn | head -10 \
  || echo "  (none)"

echo -e "\n${GREEN}🔧 Auth attempts (mobile BFF)${NC}"
docker logs --since "$WINDOW" levlab-gt-mobile 2>&1 | grep -c "POST /v1/auth/login" \
  | xargs -I {} echo "  Total login attempts: {}"

echo -e "\n${GREEN}🤖 Tool RCE attempts (DVAIA)${NC}"
docker logs --since "$WINDOW" levlab-gt-dvaia 2>&1 | grep -E "tool_call|exec_shell" | wc -l \
  | xargs -I {} echo "  tool_call/exec_shell mentions: {}"

echo -e "\n${GREEN}🔄 Tenant cross-tenant attempts${NC}"
docker logs --since "$WINDOW" levlab-gt-tenant 2>&1 | grep -E "/v1/tenants/t[0-9]" | wc -l \
  | xargs -I {} echo "  Tenant API hits: {}"

echo -e "\n${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Run as: bash triage.sh [WINDOW]   (default 1h)${NC}"
echo -e "${CYAN}Examples: bash triage.sh 24h | bash triage.sh 30m${NC}"
