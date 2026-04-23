# Leviathan Sparring Lab — openplc-hmi — OpenPLC v3 (default admin, writable registers, unsafe web admin)
# OPERATOR NOTE: OpenPLC build is heavy (~10 min). The clone uses COMMIT_SHA for reproducibility.
FROM debian:12-slim

ARG BUILD_COMMIT=unset
ARG COMMIT_SHA=b3c0de1
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    DEBIAN_FRONTEND=noninteractive

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="OpenPLC v3 — default admin:openplc creds, writable registers, unsafe web admin, Modbus exposed"

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        git curl python3 python3-pip build-essential libssl-dev \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /openplc

RUN git clone https://github.com/thiagoralves/OpenPLC_v3.git /openplc \
    && git checkout ${COMMIT_SHA} || true

# Run the install script (non-interactive)
RUN bash install.sh linux -y 2>&1 | tail -20 || true

# Seed weak credentials — OpenPLC uses SQLite DB
RUN python3 -c "
import sqlite3
conn = sqlite3.connect('/openplc/webserver/openplc.db')
# Reset admin password to 'openplc' (default, intentional)
conn.execute(\"UPDATE Users SET password='openplc' WHERE username='admin'\")
conn.commit(); conn.close()
" 2>/dev/null || true

COPY openplc-entrypoint.sh /usr/local/bin/openplc-entrypoint.sh
RUN chmod +x /usr/local/bin/openplc-entrypoint.sh

# Web: 8080, Modbus: 502
EXPOSE 8080 502

HEALTHCHECK --interval=20s --timeout=15s --retries=3 \
    CMD curl -sf http://localhost:8080/ || exit 1

ENTRYPOINT ["openplc-entrypoint.sh"]
