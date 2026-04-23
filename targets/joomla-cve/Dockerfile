# Leviathan Sparring Lab — joomla-cve — CVE-2015-8562 (PHP object injection / RCE)
# operator: pin digest via scripts/pin-digests.sh at scaffold time
FROM joomla:3.4.4

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT}

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Joomla 3.4.4 — CVE-2015-8562 PHP object injection RCE + weak admin creds"
LABEL lab.leviathan.cve="CVE-2015-8562"

# Joomla configuration with weak admin — seeded via env vars read by upstream entrypoint
ENV JOOMLA_DB_HOST=db \
    JOOMLA_DB_USER=joomla \
    JOOMLA_DB_PASSWORD=joomla \
    JOOMLA_DB_NAME=joomla \
    JOOMLA_SITE_NAME="Lab Joomla 3.4.4" \
    JOOMLA_ADMIN_USER=admin \
    JOOMLA_ADMIN_USERNAME=admin \
    JOOMLA_ADMIN_PASSWORD=admin \
    JOOMLA_ADMIN_EMAIL=admin@lab.local

EXPOSE 80

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost/administrator/ || exit 1

CMD ["apache2-foreground"]
