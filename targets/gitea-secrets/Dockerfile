# Leviathan Sparring Lab — gitea-secrets — Gitea with pre-seeded repos containing secrets
# operator: pin digest via scripts/pin-digests.sh at scaffold time
# Seed repos are injected by Ansible role seed-cicd-repos after compose up.
FROM gitea/gitea:1.21.11

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT}

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Gitea — pre-seeded repos with secrets (MinIO keys, Vault tokens, DB creds)"

ENV GITEA__database__DB_TYPE=sqlite3 \
    GITEA__database__PATH=/data/gitea/gitea.db \
    GITEA__server__DOMAIN=gitea-secrets \
    GITEA__server__HTTP_PORT=3000 \
    GITEA__server__ROOT_URL=http://gitea-secrets:3000/ \
    GITEA__security__INSTALL_LOCK=true \
    GITEA__security__SECRET_KEY=lab-gitea-secret-key-000000001 \
    GITEA__security__INTERNAL_TOKEN=lab-gitea-internal-token-0001

# Seed admin user via app.ini (Gitea reads GITEA_ADMIN_* on first run)
ENV GITEA_ADMIN_USERNAME=gitadmin \
    GITEA_ADMIN_PASSWORD=gitadmin123

EXPOSE 3000 22

HEALTHCHECK --interval=20s --timeout=10s --retries=3 \
    CMD curl -sf http://localhost:3000/api/healthz || exit 1
