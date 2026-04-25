# OPA integration

Melispy Inc. uses OPA as the policy decision point for the api-gateway. The gateway sends request context, tenant claims, and resource metadata to OPA. OPA evaluates the relevant policy package and returns an allow, deny, or block decision without embedding authorization logic in the Python services.

## Policy query paths

- Authz: `data.melispy.authz.allow`
- Authz deny signal: `data.melispy.authz.deny`
- Rate limit: `data.melispy.rate_limit.block`
- Admin allowlist: `data.melispy.admin_allowlist.allow`
- Admin deny signal: `data.melispy.admin_allowlist.deny`

## Local policy checks

Run these examples from the repository root with the `opa` CLI installed.

Authz tenant match:

```powershell
'{"method":"GET","path":["/v1","search"],"claims":{"sub":"user-1","org_id":"org-1","is_admin":false},"resource_org_id":"org-1"}' | opa eval --stdin-input --data infra/opa/policies/authz.rego "data.melispy.authz.allow"
```

Rate limit block:

```powershell
'{"request_count":101,"limit":100,"client_ip":"203.0.113.10"}' | opa eval --stdin-input --data infra/opa/policies/rate_limit.rego --data infra/opa/policies/data.json "data.melispy.rate_limit.block"
```

Admin allowlist:

```powershell
'{"path":["v1","admin"],"claims":{"is_admin":true}}' | opa eval --stdin-input --data infra/opa/policies/admin_allowlist.rego "data.melispy.admin_allowlist.allow"
```

## Bundle layout

The bundle should include the policy modules and shared data:

```text
policies/
  authz.rego
  rate_limit.rego
  admin_allowlist.rego
  data.json
```

`opa-config.yaml` points OPA at the local `melispy-bundle` service and loads `/bundles/authz.tar.gz` as the `authz` bundle. Decision logs are written to the console. The Envoy external authorization gRPC plugin listens on `:9191` and uses `data.melispy.authz.allow` as the gateway decision query.
