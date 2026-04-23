#!/usr/bin/env bash
#
# Leviathan Sparring Lab -- seed fake data into MongoDB / Redis / Elastic / MinIO / Vault
# Run AFTER `docker compose up -d` when services are healthy
#

set -e

echo "[*] Waiting for services to be ready..."
sleep 10

# ────────────────── MongoDB ──────────────────
echo "[*] Seeding MongoDB (noauth)..."
docker exec -i mongo-open mongosh --quiet --host localhost:27017 <<'MONGO'
use acme
db.users.drop()
db.users.insertMany([
  {_id:1, email:"admin@acme.example.com", password_hash:"5f4dcc3b5aa765d61d8327deb882cf99", role:"admin", mfa:false, ssn:"123-45-6789"},
  {_id:2, email:"jdoe@acme.example.com", password_hash:"e99a18c428cb38d5f260853678922e03", role:"user", mfa:false, ssn:"234-56-7890"},
  {_id:3, email:"rchen@acme.example.com", password_hash:"098f6bcd4621d373cade4e832627b4f6", role:"finance", mfa:true, ssn:"345-67-8901"},
  {_id:4, email:"pwu@acme.example.com", password_hash:"d8578edf8458ce06fbc5bb76a58c5ca4", role:"cfo", mfa:true, ssn:"456-78-9012"},
  {_id:5, email:"system@acme.example.com", password_hash:"25f9e794323b453885f5181f1b624d0b", role:"system", mfa:false, ssn:null, api_token:"svc-automation-token-FAKE-12345"}
])
db.sessions.drop()
db.sessions.insertMany([
  {_id:"sess_abc123", user_id:1, token:"eyJhbGciOiJIUzI1NiJ9.FakeJwtPayload.FakeSig", created:new Date(), expires:new Date(Date.now()+3600000)},
  {_id:"sess_xyz789", user_id:3, token:"eyJhbGciOiJIUzI1NiJ9.PayloadFinance.SignedFake", created:new Date(), expires:new Date(Date.now()+7200000)}
])
db.support_tickets.drop()
db.support_tickets.insertMany([
  {_id:1, user_id:2, subject:"Cannot access my account", body:"I forgot my password and MFA. Please reset to: MySecurePass2024!", status:"open"},
  {_id:2, user_id:3, subject:"Urgent: wire transfer", body:"Need to wire $50k to routing 021000021 account 4567891234 before EOD", status:"open"},
  {_id:3, user_id:5, subject:"Re: backup failed", body:"Backup to s3://finance-private/db-backup-2026-04-22.sql.gz failed. API key: AKIAFAKE1234567890ABCD", status:"closed"}
])
db.audit_logs.drop()
db.audit_logs.insertMany([
  {action:"login", user:"admin", ip:"192.168.1.10", at:new Date(Date.now()-86400000)},
  {action:"export_users", user:"admin", ip:"192.168.1.10", at:new Date(Date.now()-82800000), note:"exported 5000 records to /tmp/export.csv"},
  {action:"permission_change", user:"admin", target:"jdoe", before:"user", after:"admin", at:new Date(Date.now()-79200000)},
  {action:"api_key_created", user:"admin", service:"stripe", at:new Date(Date.now()-72000000)}
])
print("MongoDB seeded: " + db.users.countDocuments() + " users, " + db.sessions.countDocuments() + " sessions")
MONGO

# ────────────────── Redis ──────────────────
echo "[*] Seeding Redis (no auth)..."
docker exec -i redis-open redis-cli <<'REDIS'
FLUSHALL
SET session:abc123 "{\"user_id\":1,\"role\":\"admin\",\"expires\":9999999999}"
SET session:xyz789 "{\"user_id\":3,\"role\":\"finance\",\"expires\":9999999999}"
SET session:def456 "{\"user_id\":42,\"role\":\"contractor\",\"expires\":9999999999}"
SET oauth:token:jwt_admin "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJyb290In0.FakeSignature"
SET oauth:token:jwt_svc  "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzeXN0ZW0iLCJyb2xlIjoic3lzdGVtIn0.FakeSignatureSvc"
SET api:ratelimit:jdoe 1000
SET api:key:AKIAFAKE1234567890ABCD "{\"user\":\"jdoe\",\"scope\":\"minio:read\",\"bucket\":\"finance-private\"}"
SET config:db:primary "postgres://app:app@postgres-open:5432/megacorp"
SET config:db:replica "postgres://readonly:readonly@postgres-open:5432/megacorp"
SET secret:stripe "sk_live_FAKEStripeKey1234567890abcdefghijklmnop"
SET secret:slack:webhook "https://hooks.slack.com/services/T00000000/B00000000/FakeSlackWebhook1234567"
LPUSH queue:password_reset "{\"email\":\"jdoe@example.com\",\"token\":\"reset_abc123\"}"
LPUSH queue:password_reset "{\"email\":\"rchen@example.com\",\"token\":\"reset_xyz789\"}"
HSET cache:user:1 email "admin@acme.example.com" ssn "123-45-6789" cc "4111-1111-1111-1234"
HSET cache:user:2 email "jdoe@acme.example.com" ssn "234-56-7890" cc "4916-0000-0000-1234"
DBSIZE
REDIS

# ────────────────── Elasticsearch ──────────────────
echo "[*] Seeding Elasticsearch (no auth, no TLS)..."
sleep 3
curl -sk -X PUT http://elastic-open:9200/internal_chats -H 'Content-Type: application/json' -d '{
  "settings": { "number_of_shards": 1, "number_of_replicas": 0 }
}' >/dev/null || true

for chat in \
  '{"user":"rchen","channel":"#finance-private","text":"FYI the Q3 revenue report is at s3://finance-private/Q3-2026.xlsx — password is MegaCorp!2026","timestamp":"2026-04-20T14:32:00Z"}' \
  '{"user":"jdoe","channel":"#it-ops","text":"Vault root token rotated: hvs.FakeVaultRoot1234567890abcdefGHIJKLMN — old one still valid for 24h","timestamp":"2026-04-22T09:15:00Z"}' \
  '{"user":"admin","channel":"#alerts","text":"MinIO leak detected: finance-private bucket set to public for 3 hours. Access key: AKIAFAKE1234567890ABCD","timestamp":"2026-04-21T23:44:00Z"}' \
  '{"user":"pwu","channel":"#board-private","text":"Layoffs planned for May 15 — please do not share. Employee list: s3://hr-confidential/layoff-list-2026.csv","timestamp":"2026-04-18T16:20:00Z"}' \
  '{"user":"rchen","channel":"#engineering","text":"GitHub PAT for deploy pipeline: ghp_FakeGitHubPAT1234567890ABCDEFGHIJKLMNO","timestamp":"2026-04-19T11:08:00Z"}' \
  '{"user":"system","channel":"#alerts","text":"Backup completed: s3://backup/db-dump-2026-04-22.sql.gz (3.2GB)","timestamp":"2026-04-22T04:00:00Z"}'
do
  curl -sk -X POST http://elastic-open:9200/internal_chats/_doc -H 'Content-Type: application/json' -d "$chat" >/dev/null
done

curl -sk -X PUT http://elastic-open:9200/employee_directory -H 'Content-Type: application/json' >/dev/null || true
for emp in \
  '{"full_name":"Jennifer Chen","title":"VP Engineering","email":"jchen@megacorp.example.com","ssn":"111-22-3333","salary_usd":280000,"home_address":"1234 Elm St, Palo Alto, CA"}' \
  '{"full_name":"Ramon Serra","title":"CISO","email":"rserra@megacorp.example.com","ssn":"222-33-4444","salary_usd":310000,"home_address":"5678 Oak Ave, Menlo Park, CA"}' \
  '{"full_name":"Patricia Wu","title":"CFO","email":"pwu@megacorp.example.com","ssn":"333-44-5555","salary_usd":325000,"home_address":"9012 Pine Rd, Atherton, CA"}'
do
  curl -sk -X POST http://elastic-open:9200/employee_directory/_doc -H 'Content-Type: application/json' -d "$emp" >/dev/null
done

echo "  Elasticsearch: $(curl -sk http://elastic-open:9200/_cat/indices | wc -l) indices"

# ────────────────── MinIO ──────────────────
echo "[*] Seeding MinIO buckets..."
sleep 3

# mc (MinIO client) inside alias container
docker run --rm --network levlab_cloud_net \
  --entrypoint sh minio/mc:latest -c "
mc alias set lab http://minio-open:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD} 2>/dev/null
for b in finance-private hr-confidential ml-datasets backup public-cdn client-contracts; do
  mc mb --ignore-existing lab/\$b
done

# public policy on finance-private (misconfig)
mc anonymous set download lab/finance-private 2>/dev/null || true

# Seed fake content
echo 'Payroll Q2 2026: Jennifer Chen 280k, Ramon Serra 310k, Patricia Wu 325k, David Park 185k' | mc pipe lab/finance-private/payroll-2026-Q2.csv
echo 'M&A target list: Acme Corp, Globex Industries, Initech, Hooli. Do not share.' | mc pipe lab/finance-private/ma-targets-confidential.txt
echo 'Employee list with SSN/salary — HR only' | mc pipe lab/hr-confidential/employee-roster-2026.csv
echo 'Client: Acme Inc. MSA signed 2023, renewal 2026-12-31, revenue 2.4M/yr' | mc pipe lab/client-contracts/acme-msa.txt
echo 'db-dump-2026-04-22 (3.2GB placeholder)' | mc pipe lab/backup/db-dump-2026-04-22.sql.gz
echo 'Model: fraud-detector-v4 — training data includes customer SSN/CC (PII violation)' | mc pipe lab/ml-datasets/fraud-v4-training.parquet.meta

mc ls --recursive lab/ | head -30
"

# ────────────────── Vault ──────────────────
echo "[*] Seeding Vault (dev mode, root token in env)..."
sleep 5
docker exec vault-dev-bad vault kv put -address=http://127.0.0.1:8200 secret/prod/db \
  username=dbadmin \
  password=\$uper\$ecret2026! \
  host=postgres-open.internal \
  2>/dev/null || true

docker exec vault-dev-bad vault kv put -address=http://127.0.0.1:8200 secret/prod/aws \
  access_key=AKIAFAKEAWSPRODKEY \
  secret_key=FakeAWSSecretKey/ProdForTesting++++/abcdef123 \
  region=us-east-1 \
  2>/dev/null || true

docker exec vault-dev-bad vault kv put -address=http://127.0.0.1:8200 secret/prod/github \
  pat=ghp_FakeGitHubPAT1234567890ABCDEFGHIJKLMNO \
  org=megacorp \
  2>/dev/null || true

docker exec vault-dev-bad vault kv put -address=http://127.0.0.1:8200 secret/prod/stripe \
  secret_key=sk_live_FAKEStripeKey1234567890abcdefghijklmnop \
  webhook_secret=whsec_FakeStripeWebhook \
  2>/dev/null || true

docker exec vault-dev-bad vault kv put -address=http://127.0.0.1:8200 secret/prod/slack \
  webhook=https://hooks.slack.com/services/T00000000/B00000000/FakeSlackWebhook1234567 \
  bot_token=xoxb-fake-slack-bot-token-1234567890 \
  2>/dev/null || true

echo "  Vault secrets seeded under secret/prod/*"

# ────────────────── Gitea ──────────────────
echo "[*] Seeding Gitea (user + repo with secrets)..."
sleep 5
# Create admin user
docker exec gitea su git -c 'gitea admin user create --username platform --password FixturePw2026 --email platform@acme.example.com --admin --must-change-password=false' 2>/dev/null || true

# Create fixture user
docker exec gitea su git -c 'gitea admin user create --username jdoe --password jdoe2024 --email jdoe@acme.example.com --must-change-password=false' 2>/dev/null || true

# Generate a token for automation
TOKEN=$(docker exec gitea su git -c 'gitea admin user generate-access-token --username platform --scopes write:repository,write:user --token-name levlab-seed' 2>/dev/null | grep -oP '[a-f0-9]{40}' | head -1)

if [ -n "$TOKEN" ]; then
  # Create repo via API
  curl -sk -u "platform:FixturePw2026" -X POST http://gitea:3000/api/v1/user/repos \
    -H 'Content-Type: application/json' \
    -d '{"name":"dev-platform","description":"Internal platform tooling","private":false}' >/dev/null
fi

echo "  Gitea user + fixture repo seeded"

echo ""
echo "[OK] Seeding complete"
