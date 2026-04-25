#!/usr/bin/env bash
# Generate internal CA + per-service certs for Melispy mTLS mesh.
# V-T7-001: also generates wildcard cert (single CA flaw — intentional for pentest).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="$SCRIPT_DIR/certs"
mkdir -p "$CERTS_DIR"

SERVICES=(
    api-gateway
    auth-service
    users-service
    orgs-service
    search-service
    admin-service
    notifications-service
    agents-service
    llm-service
    billing-service
    webhooks-service
    uploads-service
)

# --- Root CA ---
if [[ ! -f "$CERTS_DIR/ca.key" ]]; then
    echo "[CA] Generating root CA..."
    openssl genrsa -out "$CERTS_DIR/ca.key" 4096
    openssl req -new -x509 -days 3650 -key "$CERTS_DIR/ca.key" \
        -out "$CERTS_DIR/ca.crt" \
        -subj "/C=UY/ST=Montevideo/O=Melispy Internal CA/CN=melispy-internal-ca"
    echo "[CA] Root CA generated."
else
    echo "[CA] Root CA already exists, skipping."
fi

# --- Per-service certs ---
for svc in "${SERVICES[@]}"; do
    CERT="$CERTS_DIR/${svc}.melispy.internal.crt"
    KEY="$CERTS_DIR/${svc}.melispy.internal.key"
    if [[ -f "$CERT" ]]; then
        echo "[CERT] ${svc}: already exists, skipping."
        continue
    fi
    echo "[CERT] Generating cert for ${svc}.melispy.internal..."
    openssl genrsa -out "$KEY" 2048
    SAN="subjectAltName=DNS:${svc}.melispy.internal,DNS:${svc},DNS:localhost"
    openssl req -new -key "$KEY" \
        -subj "/C=UY/O=Melispy/CN=${svc}.melispy.internal" | \
    openssl x509 -req -days 365 \
        -CA "$CERTS_DIR/ca.crt" -CAkey "$CERTS_DIR/ca.key" -CAcreateserial \
        -extfile <(echo "$SAN") \
        -out "$CERT"
    echo "[CERT] ${svc}: done."
done

# --- V-T7-001: Wildcard cert (intentional pentest vuln — shared across all services) ---
WILDCARD_KEY="$CERTS_DIR/wildcard.key"
WILDCARD_CERT="$CERTS_DIR/wildcard.crt"
if [[ ! -f "$WILDCARD_CERT" ]]; then
    echo "[VULN V-T7-001] Generating shared wildcard cert (*.melispy.internal)..."
    openssl genrsa -out "$WILDCARD_KEY" 2048
    openssl req -new -key "$WILDCARD_KEY" \
        -subj "/C=UY/O=Melispy/CN=*.melispy.internal" | \
    openssl x509 -req -days 365 \
        -CA "$CERTS_DIR/ca.crt" -CAkey "$CERTS_DIR/ca.key" -CAcreateserial \
        -extfile <(echo "subjectAltName=DNS:*.melispy.internal") \
        -out "$WILDCARD_CERT"
    echo "[VULN V-T7-001] Wildcard cert generated — any compromised service can impersonate all others."
fi

# Symlink ca.crt to certs dir root for Traefik mount
ln -sf "$CERTS_DIR/ca.crt" "$SCRIPT_DIR/ca.crt" 2>/dev/null || true

echo "[DONE] All certs in $CERTS_DIR"
echo "       Mount $SCRIPT_DIR into Traefik as /etc/traefik/ca"
