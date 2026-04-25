#!/usr/bin/env bash
# harden.sh — idempotent OS hardening for Debian 12 VPS Leviathan Sparring Lab v2
#
# Phases (run individually or all):
#   --phase=base       apt + unattended-upgrades + chrony + lynis
#   --phase=ssh        ssh hardening + custom port + key-only
#   --phase=ufw        firewall default-deny + allowlist
#   --phase=sysctl     kernel hardening
#   --phase=auditd     audit + aide FIM
#   --phase=fail2ban   jails ssh + traefik
#   --phase=docker     docker + userns-remap + daemon hardening
#   --phase=wireguard  install wg + interface
#   --phase=cloudflared install cloudflared
#   --phase=all        all phases (default)
#
# Idempotent: safe to re-run. Tracks state in /var/lib/levlab-harden/<phase>.done

set -euo pipefail

PHASE="${1:-all}"
PHASE="${PHASE#--phase=}"
STATE_DIR="/var/lib/levlab-harden"
LOG="/var/log/levlab-harden.log"

mkdir -p "$STATE_DIR"
exec > >(tee -a "$LOG") 2>&1

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$1] $2"; }
mark_done() { touch "$STATE_DIR/$1.done"; }
is_done() { [[ -f "$STATE_DIR/$1.done" ]]; }

if [[ $EUID -ne 0 ]]; then
    log ERROR "must run as root"
    exit 1
fi

# ─── BASE ───────────────────────────────────────────────────────────────
phase_base() {
    is_done base && { log INFO "base already done, skipping"; return; }
    log INFO "phase: base"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get upgrade -y
    apt-get install -y \
        unattended-upgrades apt-listchanges \
        chrony \
        lynis aide rkhunter \
        auditd \
        ufw fail2ban \
        wireguard wireguard-tools \
        curl wget gnupg ca-certificates \
        jq tmux htop ripgrep fd-find \
        git vim
    systemctl enable --now chrony
    cat > /etc/apt/apt.conf.d/50unattended-upgrades.local <<EOF
Unattended-Upgrade::Origins-Pattern {
    "origin=Debian,codename=\${distro_codename},label=Debian-Security";
};
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
EOF
    cat > /etc/apt/apt.conf.d/20auto-upgrades <<EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
    mark_done base
}

# ─── SSH ────────────────────────────────────────────────────────────────
phase_ssh() {
    is_done ssh && { log INFO "ssh already done, skipping"; return; }
    log INFO "phase: ssh"
    local SSH_PORT="${SSH_PORT:-49222}"
    local SSH_USER="${SSH_USER:-levop}"

    # Create non-root sudo user if absent
    if ! id "$SSH_USER" &>/dev/null; then
        useradd -m -s /bin/bash -G sudo "$SSH_USER"
        log INFO "created user $SSH_USER"
    fi

    # Copy root authorized_keys to user
    if [[ -f /root/.ssh/authorized_keys ]]; then
        mkdir -p "/home/$SSH_USER/.ssh"
        cp /root/.ssh/authorized_keys "/home/$SSH_USER/.ssh/"
        chown -R "$SSH_USER:$SSH_USER" "/home/$SSH_USER/.ssh"
        chmod 700 "/home/$SSH_USER/.ssh"
        chmod 600 "/home/$SSH_USER/.ssh/authorized_keys"
    fi

    # Sudo NOPASSWD only during bootstrap (will be tightened post-WG)
    echo "$SSH_USER ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/levlab-$SSH_USER"
    chmod 440 "/etc/sudoers.d/levlab-$SSH_USER"

    # SSH config hardening
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.$(date +%s) 2>/dev/null || true
    cat > /etc/ssh/sshd_config.d/99-levlab.conf <<EOF
Port $SSH_PORT
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
PrintMotd no
ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 3
MaxSessions 4
LoginGraceTime 30
AllowUsers $SSH_USER
Banner /etc/issue.net
EOF

    cat > /etc/issue.net <<'EOF'
*****************************************************************
                         AUTHORIZED ACCESS ONLY
  Disconnect immediately if you are not an authorized user.
  All activity is logged and monitored.
*****************************************************************
EOF

    sshd -t  # validate
    systemctl reload ssh
    log INFO "SSH on port $SSH_PORT for user $SSH_USER, root login disabled"
    mark_done ssh
}

# ─── UFW ────────────────────────────────────────────────────────────────
phase_ufw() {
    is_done ufw && { log INFO "ufw already done, skipping"; return; }
    log INFO "phase: ufw"
    local SSH_PORT="${SSH_PORT:-49222}"
    local OPERATOR_IP="${OPERATOR_IP:-179.24.190.234}"

    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    # Allow SSH from operator IP only (transitional, after WG up will tighten more)
    ufw allow from "$OPERATOR_IP" to any port "$SSH_PORT" proto tcp comment "ssh-operator"
    # Allow WireGuard
    ufw allow from "$OPERATOR_IP" to any port 51820 proto udp comment "wireguard"
    # Allow ICMP from operator
    ufw allow from "$OPERATOR_IP" proto icmp comment "icmp-operator"

    ufw logging medium
    ufw --force enable
    ufw status verbose
    mark_done ufw
}

# ─── SYSCTL ─────────────────────────────────────────────────────────────
phase_sysctl() {
    is_done sysctl && { log INFO "sysctl already done, skipping"; return; }
    log INFO "phase: sysctl"
    cat > /etc/sysctl.d/99-levlab.conf <<'EOF'
# Kernel hardening
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.yama.ptrace_scope = 2
kernel.unprivileged_bpf_disabled = 1
kernel.kexec_load_disabled = 1
kernel.sysrq = 0
fs.suid_dumpable = 0
fs.protected_hardlinks = 1
fs.protected_symlinks = 1

# Network hardening
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1

# IPv6 disable (uncomment if not used)
# net.ipv6.conf.all.disable_ipv6 = 1
# net.ipv6.conf.default.disable_ipv6 = 1
EOF
    sysctl --system >/dev/null
    mark_done sysctl
}

# ─── AUDITD ─────────────────────────────────────────────────────────────
phase_auditd() {
    is_done auditd && { log INFO "auditd already done, skipping"; return; }
    log INFO "phase: auditd + aide"

    cat > /etc/audit/rules.d/99-levlab.rules <<'EOF'
# Authentication
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/sudoers -p wa -k privesc
-w /etc/sudoers.d/ -p wa -k privesc

# SSH
-w /etc/ssh/sshd_config -p wa -k ssh-config
-w /etc/ssh/sshd_config.d/ -p wa -k ssh-config

# Privileged commands
-a always,exit -F arch=b64 -S execve -F euid=0 -k root-exec
-a always,exit -F arch=b64 -S execve -F euid!=0 -F uid=0 -k privesc-exec

# Suspicious file writes
-w /etc/cron.d/ -p wa -k cron
-w /etc/cron.daily/ -p wa -k cron
-w /etc/cron.hourly/ -p wa -k cron
-w /etc/systemd/system/ -p wa -k systemd-units
-w /tmp/ -p wa -k tmp-write
-w /dev/shm/ -p wa -k shm-write

# Make config immutable (last rule)
-e 2
EOF
    augenrules --load
    systemctl restart auditd

    # AIDE baseline
    if [[ ! -f /var/lib/aide/aide.db ]]; then
        log INFO "running aide --init (may take 5-10min)..."
        aideinit -y -f || aide --init
        cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db 2>/dev/null || true
    fi

    cat > /etc/cron.daily/aide-check <<'EOF'
#!/bin/bash
/usr/bin/aide --check 2>&1 | logger -t aide
EOF
    chmod +x /etc/cron.daily/aide-check
    mark_done auditd
}

# ─── FAIL2BAN ───────────────────────────────────────────────────────────
phase_fail2ban() {
    is_done fail2ban && { log INFO "fail2ban already done, skipping"; return; }
    log INFO "phase: fail2ban"
    local SSH_PORT="${SSH_PORT:-49222}"
    cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 3
banaction = ufw

[sshd]
enabled = true
port = $SSH_PORT
filter = sshd
logpath = %(sshd_log)s
backend = systemd
maxretry = 3

[traefik-auth]
enabled = false
# enable post deploy with traefik logs configured

[traefik-ratelimit]
enabled = false
# enable post deploy
EOF
    systemctl enable --now fail2ban
    systemctl restart fail2ban
    mark_done fail2ban
}

# ─── DOCKER ─────────────────────────────────────────────────────────────
phase_docker() {
    is_done docker && { log INFO "docker already done, skipping"; return; }
    log INFO "phase: docker"
    if ! command -v docker &>/dev/null; then
        install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
        chmod a+r /etc/apt/keyrings/docker.asc
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" \
            > /etc/apt/sources.list.d/docker.list
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    fi

    mkdir -p /etc/docker /etc/subuid.d
    cat > /etc/docker/daemon.json <<'EOF'
{
  "userland-proxy": false,
  "live-restore": true,
  "no-new-privileges": true,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "20m",
    "max-file": "3"
  },
  "icc": false,
  "iptables": true,
  "default-ulimits": {
    "nofile": { "Name": "nofile", "Hard": 65536, "Soft": 65536 }
  }
}
EOF
    # userns-remap requires care — leave commented out for now, enable manually after testing
    # echo '{"userns-remap":"default"}' | jq -s '.[0] * .[1]' /etc/docker/daemon.json - > /tmp/d.json && mv /tmp/d.json /etc/docker/daemon.json

    systemctl enable --now docker
    systemctl restart docker

    # Add ssh user to docker group
    local SSH_USER="${SSH_USER:-levop}"
    if id "$SSH_USER" &>/dev/null; then
        usermod -aG docker "$SSH_USER"
    fi
    mark_done docker
}

# ─── WIREGUARD ──────────────────────────────────────────────────────────
phase_wireguard() {
    is_done wireguard && { log INFO "wireguard already done, skipping"; return; }
    log INFO "phase: wireguard"

    if [[ ! -f /etc/wireguard/wg0.conf ]]; then
        umask 077
        local SERVER_PRIV
        SERVER_PRIV=$(wg genkey)
        local SERVER_PUB
        SERVER_PUB=$(echo "$SERVER_PRIV" | wg pubkey)

        cat > /etc/wireguard/wg0.conf <<EOF
[Interface]
PrivateKey = $SERVER_PRIV
Address = 10.8.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT

# Peer (operator laptop) — fill PublicKey via ./scripts/generate-wg-keys.sh
# [Peer]
# PublicKey = <REPLACE_WITH_OPERATOR_PUBKEY>
# AllowedIPs = 10.8.0.2/32
EOF
        chmod 600 /etc/wireguard/wg0.conf
        log INFO "WG server pubkey: $SERVER_PUB (save to .env.lab as WG_SERVER_PUBKEY)"
        echo "$SERVER_PUB" > /var/lib/levlab-harden/wg-server.pub
    fi

    systemctl enable wg-quick@wg0
    # Don't start until peer added
    log WARN "wg-quick@wg0 NOT started yet — add operator peer to /etc/wireguard/wg0.conf first"
    mark_done wireguard
}

# ─── CLOUDFLARED ────────────────────────────────────────────────────────
phase_cloudflared() {
    is_done cloudflared && { log INFO "cloudflared already done, skipping"; return; }
    log INFO "phase: cloudflared"
    if ! command -v cloudflared &>/dev/null; then
        curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
            | tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
        echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared bookworm main" \
            > /etc/apt/sources.list.d/cloudflared.list
        apt-get update
        apt-get install -y cloudflared
    fi
    log INFO "cloudflared installed. Tunnel runs as docker container, not host service."
    mark_done cloudflared
}

# ─── DISPATCH ───────────────────────────────────────────────────────────
case "$PHASE" in
    base)         phase_base ;;
    ssh)          phase_ssh ;;
    ufw)          phase_ufw ;;
    sysctl)       phase_sysctl ;;
    auditd)       phase_auditd ;;
    fail2ban)     phase_fail2ban ;;
    docker)       phase_docker ;;
    wireguard)    phase_wireguard ;;
    cloudflared)  phase_cloudflared ;;
    all)
        phase_base
        phase_ssh
        phase_ufw
        phase_sysctl
        phase_auditd
        phase_fail2ban
        phase_docker
        phase_wireguard
        phase_cloudflared
        log INFO "all phases done. Run: lynis audit system"
        ;;
    *)
        echo "Usage: $0 [--phase=base|ssh|ufw|sysctl|auditd|fail2ban|docker|wireguard|cloudflared|all]"
        exit 1
        ;;
esac
