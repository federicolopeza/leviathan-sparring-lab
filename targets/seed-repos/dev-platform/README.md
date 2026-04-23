# dev-platform

Internal platform tooling for Leviathan Inc.

Manages infrastructure provisioning, MinIO object storage configuration,
and Vault secret engine bootstrapping for the lab environment.

## Structure

- `terraform/` — IaC for cloud resource provisioning
- `src/` — Node/Express service reading object-store credentials
- `.gitlab-ci.yml` — CI pipeline (GitLab runner)

## Setup

```bash
npm install
node src/app.js
```

Requires: `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `VAULT_TOKEN` in environment.
