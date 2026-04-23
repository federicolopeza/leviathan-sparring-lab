# Leviathan Sparring Lab — bwapp — buggy web application (intentional, >100 vulns)
# operator: pin digest via scripts/pin-digests.sh at scaffold time
FROM php:5.6-apache

ARG BUILD_COMMIT=unset
ARG BWAPP_COMMIT=main
ENV BUILD_COMMIT=${BUILD_COMMIT}

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="bWAPP — XXE, SSTI, SQLi, XSS, auth flaws — all security levels"

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        git curl mariadb-client libpng-dev \
    && docker-php-ext-install pdo pdo_mysql mysql mysqli \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/raesene/bWAPP.git /bwapp-src \
    && cp -r /bwapp-src/bWAPP/. /var/www/html/ \
    && chown -R www-data:www-data /var/www/html \
    && rm -rf /bwapp-src

COPY bwapp-settings.php /var/www/html/settings.php

# bWAPP install script runs on first request — set low security
RUN sed -i 's/\$security_level = .*/\$security_level = "0";/' /var/www/html/settings.php 2>/dev/null || true

EXPOSE 80

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost/login.php || exit 1

CMD ["apache2-foreground"]
