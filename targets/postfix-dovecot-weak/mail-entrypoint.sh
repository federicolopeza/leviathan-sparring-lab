#!/usr/bin/env bash
set -e

# Create lab mail users with weak passwords (intentional)
for user in admin operator labuser; do
    id -u "$user" &>/dev/null || useradd -m -s /sbin/nologin "$user"
    echo "$user:password123" | chpasswd
    mkdir -p "/var/mail/$user"
    chown "$user:$user" "/var/mail/$user"
done

# Write dovecot passwd file: username:{PLAIN}password:uid:gid::maildir
cat > /etc/dovecot/users <<EOF
admin:{PLAIN}admin:$(id -u admin):$(id -g admin)::
operator:{PLAIN}password123:$(id -u operator):$(id -g operator)::
labuser:{PLAIN}labuser:$(id -u labuser):$(id -g labuser)::
EOF

postfix start
dovecot

# Keep container alive
tail -f /var/log/mail.log 2>/dev/null || sleep infinity
