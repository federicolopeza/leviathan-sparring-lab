# Leviathan Sparring Lab — wordpress-cve — CVE-2019-8942 / CVE-2019-8943 (image upload RCE)
# operator: pin digest via scripts/pin-digests.sh at scaffold time
FROM wordpress:5.0.0-apache

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT}

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="WordPress 5.0.0 — CVE-2019-8942/8943 image upload RCE + XML-RPC + weak creds"
LABEL lab.leviathan.cve="CVE-2019-8942,CVE-2019-8943"

# Install WP-CLI + enable XML-RPC + leave config backup as exposure
RUN curl -sL https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar -o /usr/local/bin/wp \
    && chmod +x /usr/local/bin/wp \
    && apt-get update -qq && apt-get install -y --no-install-recommends less mariadb-client \
    && rm -rf /var/lib/apt/lists/*

# XML-RPC must be reachable; drop an .htaccess that un-blocks xmlrpc.php
RUN echo "Order allow,deny\nAllow from all" > /var/www/html/xmlrpc-allow.conf

# Fake wp-config backup (GT-WP-005)
COPY wp-config.php.bak /var/www/html/wp-config.php.bak

COPY docker-entrypoint-wp.sh /usr/local/bin/docker-entrypoint-wp.sh
RUN chmod +x /usr/local/bin/docker-entrypoint-wp.sh

EXPOSE 80

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost/wp-login.php || exit 1

ENTRYPOINT ["docker-entrypoint-wp.sh"]
CMD ["apache2-foreground"]
