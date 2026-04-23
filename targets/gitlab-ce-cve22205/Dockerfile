# Leviathan Sparring Lab — gitlab-ce-cve22205 — GitLab CE 13.9.0 CVE-2021-22205 (ExifTool RCE)
# operator: pin digest via scripts/pin-digests.sh at scaffold time
FROM gitlab/gitlab-ce:13.9.0-ce.0

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT}

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="GitLab CE 13.9.0 — CVE-2021-22205 ExifTool RCE via image upload"
LABEL lab.leviathan.cve="CVE-2021-22205"

# Seed root password via GITLAB_ROOT_PASSWORD env
ENV GITLAB_ROOT_PASSWORD=LabPassword123! \
    GITLAB_OMNIBUS_CONFIG="gitlab_rails['initial_root_password'] = 'LabPassword123!'; nginx['redirect_http_to_https'] = false;"

EXPOSE 80 443 22

HEALTHCHECK --interval=20s --timeout=30s --retries=5 \
    CMD curl -sf http://localhost/-/health || exit 1
