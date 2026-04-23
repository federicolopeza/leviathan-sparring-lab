#!/usr/bin/env bash
set -e

# Run the upstream WordPress entrypoint first to configure wp-config.php
source /usr/local/bin/docker-entrypoint.sh

# Wait for MySQL then seed admin:admin + weak user
( sleep 20 && \
  wp --allow-root --path=/var/www/html core install \
     --url="http://localhost" \
     --title="Lab WP 5.0.0" \
     --admin_user=admin \
     --admin_password=admin \
     --admin_email=admin@lab.local \
     --skip-email 2>/dev/null || true \
) &

exec "$@"
