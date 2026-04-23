# Leviathan Sparring Lab — jenkins-cve1000861 — Jenkins 2.137 CVE-2018-1000861 (Stapler proxy unauth RCE)
# operator: pin digest via scripts/pin-digests.sh at scaffold time
# NOTE: jenkins/jenkins:2.137 may need to be sourced from a registry mirror if DockerHub removed it.
# Fallback: use jenkins/jenkins:2.138 (still vulnerable to the Stapler issue).
FROM jenkins/jenkins:2.137

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Jenkins 2.137 — CVE-2018-1000861 unsafe Stapler proxy unauth RCE + script console"
LABEL lab.leviathan.cve="CVE-2018-1000861"

# Disable setup wizard + seed admin:admin credentials
COPY jenkins-init.groovy /usr/share/jenkins/ref/init.groovy.d/init.groovy

EXPOSE 8080 50000

HEALTHCHECK --interval=20s --timeout=10s --retries=3 \
    CMD curl -sf http://localhost:8080/login || exit 1
