# 11 — Operations (scripts + Makefile)

Pegamento entre infra y benchmark. Todo automatizado.

## Scripts en `scripts/`

```
scripts/
├── bootstrap.sh                 # one-shot: preflight → apply → ansible → up → smoke
├── teardown.sh                  # export + destroy + rotate keys
├── smoke.sh                     # 8-check GATE (ver 06-observability.md)
├── kill.sh                      # kill-switch toggle
├── vultr-preflight.sh           # valida Vultr + CF + tf plan dry-run
├── export-artifacts.sh          # rsync + hash-chain verify gate
├── build-scoreboard.py          # findings × GT → CSV
├── generate-wg-keys.sh          # WG server keypair
├── reconcile.py                 # findings ↔ GT reconciliation
└── validate-ground-truth.py     # ground_truth.yml schema check
```

## `scripts/bootstrap.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

test -f .env.lab || { echo "[FAIL] .env.lab missing. Copy .env.lab.example → .env.lab + fill"; exit 1; }
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
```

## `scripts/vultr-preflight.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
source .env.lab

echo "[*] Vultr preflight..."

# 1. API key válida
vultr-cli account get >/dev/null || { echo "[FAIL] Vultr API key rejected"; exit 1; }

# 2. Plan disponible en región
plan_avail=$(vultr-cli plans list | awk -v plan="$VULTR_PLAN" '$1==plan{print $NF}')
if [[ -z "$plan_avail" ]]; then
  echo "[FAIL] Plan $VULTR_PLAN not available. Alternatives:"
  vultr-cli plans list | grep -i '8c' | head -5
  exit 1
fi

# 3. OS ID = Debian 12
os_check=$(vultr-cli os list | awk -v id="$VULTR_OS_ID" '$1==id{print $2}')
[[ "$os_check" == "Debian" ]] || { echo "[FAIL] OS ID $VULTR_OS_ID not Debian"; exit 1; }

# 4. Región tiene plan
region_avail=$(vultr-cli plans list --region "$VULTR_REGION" | grep "$VULTR_PLAN" || true)
[[ -n "$region_avail" ]] || { echo "[FAIL] Plan $VULTR_PLAN not in region $VULTR_REGION"; exit 1; }

# 5. CF zone matchea BASE_DOMAIN
cf_zone=$(curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID" | jq -r '.result.name')
[[ "$cf_zone" == "$BASE_DOMAIN" ]] || {
  echo "[FAIL] CF_ZONE_ID $CF_ZONE_ID resolves to '$cf_zone', expected '$BASE_DOMAIN'"
  exit 1
}

# 6. WG keys present or generate
if [[ -z "${WG_SERVER_PRIVATE_KEY:-}" ]]; then
  echo "[*] Generating WG server keypair..."
  ./scripts/generate-wg-keys.sh
fi

# 7. Auto-detect operator IP if empty
if [[ -z "${OPERATOR_PUBLIC_IP:-}" ]]; then
  OPERATOR_PUBLIC_IP=$(curl -s https://cloudflare.com/cdn-cgi/trace | awk -F= '/^ip=/{print $2}')
  echo "[*] Auto-detected OPERATOR_PUBLIC_IP=$OPERATOR_PUBLIC_IP"
  sed -i "s/^OPERATOR_PUBLIC_IP=.*/OPERATOR_PUBLIC_IP=$OPERATOR_PUBLIC_IP/" .env.lab
fi

# 8. terraform plan dry-run
cd terraform
terraform init -upgrade
terraform plan -out=/tmp/levlab.tfplan \
  -var "vultr_api_key=$VULTR_API_KEY" \
  -var "cloudflare_api_token=$CF_API_TOKEN" \
  -var "cloudflare_zone_id=$CF_ZONE_ID" \
  -var "cloudflare_account_id=$CF_ACCOUNT_ID" \
  -var "base_domain=$BASE_DOMAIN" \
  -var "vultr_region=$VULTR_REGION" \
  -var "vultr_plan=$VULTR_PLAN" \
  -var "vultr_os_id=$VULTR_OS_ID" \
  -var "operator_public_ip=$OPERATOR_PUBLIC_IP" \
  -var "ssh_public_key=$(cat $SSH_PUBLIC_KEY_PATH)" >/dev/null

echo "[OK] Preflight passed. terraform plan saved to /tmp/levlab.tfplan"
echo "[*] Estimated cost: \$$(echo "scale=2; 0.143 * 24" | bc) compute + ≤\$0.60 bandwidth"
```

## `scripts/export-artifacts.sh` (hash-chain gated)

```bash
#!/usr/bin/env bash
set -euo pipefail
source .env.lab

SERVER_IP="$(cd terraform && terraform output -raw server_ipv4)"
DEST="artifacts/${RUN_ID}"
mkdir -p "$DEST"

# 1. rsync evidence vía wg0 (NO public IP)
rsync -avz -e "ssh -i $SSH_PRIVATE_KEY_PATH -o StrictHostKeyChecking=no" \
  leviathan@10.88.0.1:/opt/levlab/artifacts/ "$DEST/"

# 2. Verify hash-chain ANTES de permitir teardown
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
```

## `scripts/teardown.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

test -f .env.lab || { echo ".env.lab missing"; exit 1; }
set -a; source .env.lab; set +a

echo "[*] Exporting artifacts (hash-chain gated)..."
./scripts/export-artifacts.sh

echo "[*] docker compose down..."
make down || true

echo "[*] terraform destroy..."
make destroy

echo "[*] Verify Vultr resources = 0..."
vultr-cli instance list --output json \
  | jq -e --arg lbl "$VULTR_INSTANCE_LABEL" '[.instances[] | select(.label==$lbl)] | length == 0' \
  || { echo "[FAIL] Vultr instance still present. Manual cleanup needed."; exit 1; }

echo "[*] Cloudflare DNS cleanup verify..."
curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records?name=lab.$BASE_DOMAIN" \
  | jq -e '.result | length == 0' \
  || { echo "[WARN] DNS records remain — manual cleanup"; }

echo "[*] Cloudflare Tunnel revoke..."
cloudflared tunnel delete "$CF_TUNNEL_ID" --force || true

echo "[*] WireGuard key rotation..."
./scripts/generate-wg-keys.sh --rotate

echo "[OK] Teardown complete. Resources=0. Ready for next ephemeral session."
```

## `scripts/kill.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
source .env.lab

SERVER_IP="$(cd terraform && terraform output -raw server_ipv4)"
ssh -i "$SSH_PRIVATE_KEY_PATH" -o StrictHostKeyChecking=no leviathan@10.88.0.1 \
  'sudo touch /opt/levlab/KILL_SWITCH && \
   sudo docker compose -f /opt/levlab/docker-compose.yml exec traefik touch /logs/kill-active'
echo "[KILL] marker set. Pipeline aborts on next tool_result."
echo "[*] To resume:"
echo "  ssh leviathan@10.88.0.1 'sudo rm /opt/levlab/KILL_SWITCH'"
```

## `scripts/generate-wg-keys.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-generate}"

if [[ "$MODE" == "--rotate" ]]; then
  echo "[*] Rotating WG keys (new server keypair, archiving old)..."
  cp .env.lab ".env.lab.rotated.$(date +%s)"
fi

# Generate new server keypair
WG_SERVER_PRIVATE=$(wg genkey)
WG_SERVER_PUBLIC=$(echo "$WG_SERVER_PRIVATE" | wg pubkey)

# Update .env.lab in place
if grep -q "^WG_SERVER_PRIVATE_KEY=" .env.lab; then
  sed -i "s|^WG_SERVER_PRIVATE_KEY=.*|WG_SERVER_PRIVATE_KEY=$WG_SERVER_PRIVATE|" .env.lab
  sed -i "s|^WG_SERVER_PUBLIC_KEY=.*|WG_SERVER_PUBLIC_KEY=$WG_SERVER_PUBLIC|" .env.lab
else
  echo "WG_SERVER_PRIVATE_KEY=$WG_SERVER_PRIVATE" >> .env.lab
  echo "WG_SERVER_PUBLIC_KEY=$WG_SERVER_PUBLIC" >> .env.lab
fi

echo "[OK] WG server keypair generated"
echo "    public: $WG_SERVER_PUBLIC"
echo ""
echo "Operator: add this pubkey to your laptop's wg0 config as [Peer] PublicKey"
```

## Makefile (completo)

Ver [02-infrastructure.md](02-infrastructure.md#makefile) — targets: `preflight`, `init`, `apply`, `ansible`, `up`, `smoke`, `down`, `destroy`, `kill`, `full`, `teardown`.

## Flujo one-shot

Operador ejecuta desde laptop:

```bash
cd leviathan-sparring-lab/
cp .env.lab.example .env.lab
vim .env.lab                      # llenar credenciales
./scripts/bootstrap.sh            # todo hasta smoke green
```

Hora 30 min después: lab listo. Kickoff Leviathan desde CLI.

## Durante corrida — comandos útiles

```bash
# Tier hot-swap
curl -X POST http://127.0.0.1:3456/api/mythos-level -d '{"level":"WARFARE"}'
curl -X POST http://127.0.0.1:3456/api/autochain-level -d '{"level":4}'

# Force restart para propagación total env
curl -X POST http://127.0.0.1:3456/api/session/restart

# Bandwidth check
ssh leviathan@10.88.0.1 'vnstat -i eth0 --json' | jq '.interfaces[0].traffic.total'

# Live findings count
ssh leviathan@10.88.0.1 'wc -l /opt/levlab/artifacts/findings.json'

# Telemetry trail
ssh leviathan@10.88.0.1 'tail -f /opt/levlab/artifacts/skill-telemetry.jsonl'

# Kill-switch
./scripts/kill.sh

# Clear kill
ssh leviathan@10.88.0.1 'sudo rm /opt/levlab/KILL_SWITCH'
```

## Rotation policy

Post-teardown, WG keys auto-rotadas. CF tunnel token revocado. Vultr API key — operador decide si rotar (no default, lo hace tras 3 corridas para higiene).

## Recovery de corrida rota

Si algo falla mid-run y no querés perder artifacts:

```bash
# Mid-run artifact snapshot (sin teardown)
./scripts/export-artifacts.sh

# Resume después de kill-switch
ssh leviathan@10.88.0.1 'sudo rm /opt/levlab/KILL_SWITCH'
# Leviathan retoma próximo tool_result

# Si smoke fallo post-deploy pero Docker OK:
ssh leviathan@10.88.0.1 'sudo docker compose -f /opt/levlab/docker-compose.yml restart <servicio>'
./scripts/smoke.sh
```
