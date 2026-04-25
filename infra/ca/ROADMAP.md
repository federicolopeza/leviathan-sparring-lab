# Internal CA Roadmap — V-T7-001 Design

## Current State (v3.0.0 — intentionally weak)

Single self-signed CA issues one wildcard cert used by **all** internal services for mTLS.

```
infra/ca/
├── ca.crt          # Self-signed root CA
├── ca.key          # CA private key (readable by any service with volume mount)
├── wildcard.crt    # *.melispy.internal — issued to every service
└── wildcard.key    # Shared private key — same cert for api-gateway, auth, admin, etc.
```

**V-T7-001 Intentional Vuln**: Any service that is compromised (e.g., via V-T6-001 SSTI in
agents-service) can read `wildcard.key` and impersonate **any other service** in the mesh.
The cert has `SubjectAltName: *.melispy.internal` so it's valid for all internal hostnames.

Exploit path:
1. RCE in agents-service (V-T6-001)
2. Read `/etc/traefik/ca/wildcard.key` (mounted read-only into agents container)
3. Forge TLS client cert for `admin.melispy.internal`
4. Call admin-service endpoints directly, bypassing Traefik auth middleware

## Phase 5 Target (hardened)

Per-service certs issued from a proper CA hierarchy:

```
Root CA (offline)
└── Intermediate CA (online, Vault PKI)
    ├── api-gateway.melispy.internal
    ├── auth-service.melispy.internal
    ├── admin-service.melispy.internal
    └── ... (one cert per service, 30-day TTL, auto-rotated via Vault Agent)
```

V-T5-006 (shared cert) remains baked as a finding until Phase 5 deploys per-service certs.
