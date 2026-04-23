# Leviathan Sparring Lab — samba-ad-weak — Samba AD DC (weak pw policy, LDAP anon bind, SMB shares)
FROM debian:12-slim

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT}

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Samba AD DC — weak password policy, LDAP anonymous bind, exposed SMB shares"

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        samba samba-common samba-ad-dc krb5-user winbind dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Provision the AD DC with weak defaults
RUN samba-tool domain provision \
        --realm=LAB.LOCAL \
        --domain=LAB \
        --adminpass='Admin1234!' \
        --dns-backend=SAMBA_INTERNAL \
        --use-rfc2307 \
        --server-role=dc \
    || true

COPY smb.conf /etc/samba/smb.conf
COPY samba-entrypoint.sh /usr/local/bin/samba-entrypoint.sh
RUN chmod +x /usr/local/bin/samba-entrypoint.sh

EXPOSE 53/udp 53/tcp 88 135 139 389 445 464 636 3268 3269

HEALTHCHECK --interval=20s --timeout=10s --retries=3 \
    CMD samba-tool domain info 127.0.0.1 2>/dev/null || exit 1

ENTRYPOINT ["samba-entrypoint.sh"]
