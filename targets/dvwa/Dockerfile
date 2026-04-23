# Leviathan Sparring Lab — dvwa — Damn Vulnerable Web Application (intentional, security level=low)
# operator: pin digest via scripts/pin-digests.sh at scaffold time
FROM php:7.4-apache

ARG BUILD_COMMIT=unset
ARG DVWA_COMMIT=d80c3c7
ENV BUILD_COMMIT=${BUILD_COMMIT}

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="DVWA — SQLi, XSS, CSRF, file upload, cmd injection — security level low"

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        git curl mariadb-client libpng-dev libjpeg-dev \
    && docker-php-ext-install pdo pdo_mysql gd mysqli \
    && rm -rf /var/lib/apt/lists/*

# Clone pinned DVWA commit
RUN git clone https://github.com/digininja/DVWA.git /var/www/html \
    && cd /var/www/html && git checkout ${DVWA_COMMIT}

# Configure DVWA — low security, auto-populate DB
COPY dvwa-config.inc.php /var/www/html/config/config.inc.php

RUN cp /var/www/html/config/config.inc.php.dist /var/www/html/config/config.inc.php.dist.bak 2>/dev/null || true \
    && chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html \
    && chmod 777 /var/www/html/hackable/uploads /var/www/html/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt 2>/dev/null || true

EXPOSE 80

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost/login.php || exit 1

CMD ["apache2-foreground"]
