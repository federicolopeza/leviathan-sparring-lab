# Leviathan Sparring Lab — asterisk-weak — Asterisk (weak SIP, AMI exposed, call routing abuse)
FROM debian:12-slim

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    DEBIAN_FRONTEND=noninteractive

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Asterisk — weak SIP credentials, AMI exposed on 5038, call routing abuse, EAVESDROP"

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        asterisk asterisk-config \
    && rm -rf /var/lib/apt/lists/*

COPY asterisk-sip.conf        /etc/asterisk/sip.conf
COPY asterisk-extensions.conf /etc/asterisk/extensions.conf
COPY asterisk-manager.conf    /etc/asterisk/manager.conf
COPY asterisk-entrypoint.sh   /usr/local/bin/asterisk-entrypoint.sh
RUN chmod +x /usr/local/bin/asterisk-entrypoint.sh

# SIP: 5060, AMI: 5038, RTP: 10000-10100
EXPOSE 5060/udp 5060/tcp 5038 10000-10100/udp

HEALTHCHECK --interval=20s --timeout=10s --retries=3 \
    CMD asterisk -rx 'core show version' || exit 1

ENTRYPOINT ["asterisk-entrypoint.sh"]
