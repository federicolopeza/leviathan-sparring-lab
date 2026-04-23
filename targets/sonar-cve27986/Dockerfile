# Leviathan Sparring Lab — sonar-cve27986 — SonarQube 7.9 CVE-2020-27986 (unauth project/scan data exposure)
# operator: pin digest via scripts/pin-digests.sh at scaffold time
FROM sonarqube:7.9-community

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT}

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="SonarQube 7.9 — CVE-2020-27986 unauthenticated project browse + scan data exposure"
LABEL lab.leviathan.cve="CVE-2020-27986"

# Default admin:admin (SonarQube 7.9 default — intentional)
ENV SONAR_FORCEAUTHENTICATION=false \
    SONAR_SEARCH_JAVAADDITIONALOPTS="-Dnode.store.allow_mmap=false"

EXPOSE 9000

HEALTHCHECK --interval=20s --timeout=15s --retries=5 \
    CMD curl -sf http://localhost:9000/api/system/status | grep -q '"status":"UP"' || exit 1
