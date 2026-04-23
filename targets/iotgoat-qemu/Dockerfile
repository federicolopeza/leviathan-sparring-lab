# Leviathan Sparring Lab — iotgoat-qemu — IoTGoat firmware in QEMU mips
# OPERATOR NOTE: IoTGoat firmware is NOT downloaded automatically during build.
# Before building, download the IoTGoat firmware image:
#   curl -Lo targets/iotgoat-qemu/firmware/IoTGoat-raspberry-pi2.img \
#     https://github.com/OWASP/IoTGoat/releases/download/v1.0/IoTGoat-raspberry-pi2.img
# Then docker build will COPY it in. If firmware/ is absent, the build will fail with a
# helpful error. See https://github.com/OWASP/IoTGoat for firmware download instructions.
FROM debian:12-slim

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    DEBIAN_FRONTEND=noninteractive

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="IoTGoat — OWASP IoT firmware in QEMU (hardcoded creds, telnetd, insecure services)"

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        qemu-system-mips qemu-utils curl wget \
    && rm -rf /var/lib/apt/lists/*

# Operator must pre-download firmware to targets/iotgoat-qemu/firmware/
COPY firmware/ /opt/iotgoat/firmware/

COPY iotgoat-run.sh /usr/local/bin/iotgoat-run.sh
RUN chmod +x /usr/local/bin/iotgoat-run.sh

# telnetd forwarded to 2323, HTTP to 8080
EXPOSE 2323 8080

HEALTHCHECK --interval=20s --timeout=15s --retries=3 \
    CMD nc -z localhost 2323 || exit 1

ENTRYPOINT ["iotgoat-run.sh"]
