#!/usr/bin/env bash
set -e

# Create anonymous share directory
mkdir -p /srv/samba/public
chmod 777 /srv/samba/public
echo "lab-secret-share-file: MinIO root key = minio-root-key-lab001" > /srv/samba/public/credentials.txt

# Seed weak lab users
samba-tool user create labuser1 "Password1" --given-name=Lab --surname=User1 2>/dev/null || true
samba-tool user create labuser2 "lab" --given-name=Lab --surname=User2 2>/dev/null || true  # Intentional: 3-char password

exec samba --foreground --no-process-group
