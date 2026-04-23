# Leviathan Sparring Lab — mutillidae — OWASP Mutillidae II (intentional, all OWASP Top 10)
# operator: pin digest via scripts/pin-digests.sh at scaffold time
FROM php:7.4-apache

ARG BUILD_COMMIT=unset
ARG MUTILLIDAE_COMMIT=main
ENV BUILD_COMMIT=${BUILD_COMMIT}

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Mutillidae II — login bypass, XSS, SQLi, cmd exec, CSRF"

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        git curl mariadb-client libpng-dev \
    && docker-php-ext-install pdo pdo_mysql mysqli \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/webpwnized/mutillidae.git /var/www/html \
    && chown -R www-data:www-data /var/www/html

# Set DB config — mutillidae reads from database.php
COPY mutillidae-database.php /var/www/html/includes/database-config.inc

EXPOSE 80

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost/index.php || exit 1

CMD ["apache2-foreground"]
