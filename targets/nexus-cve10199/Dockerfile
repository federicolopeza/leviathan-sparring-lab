# Leviathan Sparring Lab — nexus-cve10199 — Nexus Repository 3.20.0 CVE-2020-10199 (RCE via EL injection)
# operator: pin digest via scripts/pin-digests.sh at scaffold time
FROM sonatype/nexus3:3.20.0

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT}

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Nexus Repository 3.20.0 — CVE-2020-10199 EL injection RCE"
LABEL lab.leviathan.cve="CVE-2020-10199"

# Default admin credentials: admin / admin123 (Nexus 3.20 default before first-run change)
# The admin.password file is created by Nexus on first boot — expose it at known path
ENV INSTALL4J_ADD_VM_PARAMS="-Xms512m -Xmx1g -XX:MaxDirectMemorySize=512m -Djava.util.prefs.userRoot=/nexus-data/javaprefs"

EXPOSE 8081

HEALTHCHECK --interval=20s --timeout=15s --retries=5 \
    CMD curl -sf http://localhost:8081/service/rest/v1/status || exit 1
