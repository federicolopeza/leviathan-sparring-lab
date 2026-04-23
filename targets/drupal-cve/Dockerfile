# Leviathan Sparring Lab — drupal-cve — CVE-2018-7600 Drupalgeddon 2 (unauth RCE)
# operator: pin digest via scripts/pin-digests.sh at scaffold time
FROM drupal:7.58-apache

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT}

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Drupal 7.58 — CVE-2018-7600 Drupalgeddon 2 unauthenticated RCE"
LABEL lab.leviathan.cve="CVE-2018-7600"

RUN apt-get update -qq && apt-get install -y --no-install-recommends mariadb-client curl \
    && rm -rf /var/lib/apt/lists/*

# Pre-configure settings.php with lab DB connection
COPY settings.php /var/www/html/sites/default/settings.php
RUN chmod 444 /var/www/html/sites/default/settings.php

EXPOSE 80

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost/ || exit 1

CMD ["apache2-foreground"]
