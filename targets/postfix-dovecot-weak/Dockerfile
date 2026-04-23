# Leviathan Sparring Lab — postfix-dovecot-weak — Postfix+Dovecot (STARTTLS optional, weak SASL, VRFY on)
FROM debian:12-slim

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    DEBIAN_FRONTEND=noninteractive

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Postfix + Dovecot — STARTTLS optional, weak SASL, VRFY enabled, user enumeration surface"

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        postfix postfix-doc dovecot-core dovecot-imapd dovecot-pop3d \
        libsasl2-modules sasl2-bin ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY postfix-main.cf /etc/postfix/main.cf
COPY postfix-master.cf /etc/postfix/master.cf
COPY dovecot.conf /etc/dovecot/dovecot.conf
COPY mail-entrypoint.sh /usr/local/bin/mail-entrypoint.sh
RUN chmod +x /usr/local/bin/mail-entrypoint.sh

EXPOSE 25 110 143 587 993 995

HEALTHCHECK --interval=20s --timeout=10s --retries=3 \
    CMD postfix status || exit 1

ENTRYPOINT ["mail-entrypoint.sh"]
