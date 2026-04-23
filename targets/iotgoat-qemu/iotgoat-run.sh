#!/usr/bin/env bash
# Run IoTGoat firmware in QEMU mips
set -e

FW=$(ls /opt/iotgoat/firmware/*.img 2>/dev/null | head -1)
if [ -z "$FW" ]; then
    echo "[iotgoat] ERROR: No firmware image found in /opt/iotgoat/firmware/"
    echo "[iotgoat] Download from https://github.com/OWASP/IoTGoat/releases"
    exit 1
fi

echo "[iotgoat] Starting firmware: $FW"
exec qemu-system-mips \
    -M malta \
    -kernel /usr/lib/qemu/qemu-mips-static 2>/dev/null || \
exec qemu-system-mipsel \
    -M malta \
    -hda "$FW" \
    -append "root=/dev/sda console=ttyS0" \
    -net nic \
    -net user,hostfwd=tcp::2323-:23,hostfwd=tcp::8080-:80 \
    -nographic
