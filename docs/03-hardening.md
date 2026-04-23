# 03 — Hardening host

Paranoia máxima por fuera. Filosofía **control plane rootless + target plane rootful con userns-remap**.

## Package baseline

```bash
apt-get install -y \
  ca-certificates curl wget gnupg jq unzip lsb-release apt-transport-https \
  vim-tiny less tmux htop git rsyslog logrotate chrony vnstat \
  ufw nftables iptables arptables ebtables ipset \
  apparmor apparmor-utils auditd audispd-plugins aide aide-common \
  rkhunter chkrootkit lynis fail2ban wireguard wireguard-tools \
  unattended-upgrades apt-listchanges needrestart python3 python3-pip
```

**Removido vs Plan 1:** `tripwire`. Redundante con AIDE + requiere passphrase interactiva + suma 3 min bootstrap.

## Repos adicionales

- Docker (bookworm stable, keyring)
- CrowdSec (packagecloud)
- Falco (falco.org)

## Users

```bash
useradd -m -s /bin/bash leviathan
usermod -aG sudo leviathan
passwd -l root
loginctl enable-linger leviathan
```

## sysctl `/etc/sysctl.d/99-levlab-hardening.conf`

```conf
kernel.kptr_restrict=2
kernel.dmesg_restrict=1
kernel.randomize_va_space=2
kernel.yama.ptrace_scope=2
kernel.unprivileged_bpf_disabled=1
kernel.unprivileged_userns_clone=1
fs.protected_hardlinks=1
fs.protected_symlinks=1
fs.suid_dumpable=0

net.ipv4.ip_forward=1
net.ipv4.tcp_syncookies=1
net.ipv4.conf.all.rp_filter=1
net.ipv4.conf.all.accept_source_route=0
net.ipv4.conf.all.accept_redirects=0
net.ipv4.conf.all.send_redirects=0
net.ipv4.conf.all.log_martians=1
net.ipv4.icmp_echo_ignore_broadcasts=1

net.ipv6.conf.all.accept_ra=0
net.ipv6.conf.all.accept_redirects=0

vm.mmap_rnd_bits=32
user.max_user_namespaces=28633
```

## auditd rules `/etc/audit/rules.d/99-levlab.rules`

Watches: identidad (passwd/shadow/sudoers), red (iptables/nft/ufw/nftables.conf), docker (binarios + /var/lib/docker), cloudflared, wireguard, ssh, integridad (aide/rkhunter). Syscalls execve b64/b32, mount, init_module, ptrace.

Full ruleset en `ansible/templates/99-levlab.rules.j2`.

## Firewall dual — UFW + nftables

**UFW bootstrap** — SSH del operador + HTTPS egress para pulls.
**UFW locked** — SSH sólo vía wg0 + egress a DNS/NTP/tunnel.
**nftables** enforcement fino para Docker + `DOCKER-USER` (ver [01-architecture.md](01-architecture.md)).

Transición bootstrap→locked la hace Ansible post-cloudflared healthy + wg0 up + operator verificado en `10.88.0.2`.

## AIDE baseline (reemplaza Tripwire dual)

```bash
aideinit
cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
chmod 600 /var/lib/aide/aide.db

# hourly cron durante benchmark
echo '0 * * * * root /usr/bin/aide --check > /opt/levlab/artifacts/defensive/aide-$(date +\%Y\%m\%d\%H).log 2>&1' \
  > /etc/cron.d/levlab-aide
```

## AppArmor — 2 perfiles

`/etc/apparmor.d/levlab-web` — para apps HTTP (deny sys_admin/ptrace/dac_override, deny /proc wr, /sys rwklx).
`/etc/apparmor.d/levlab-db` — para DBs (deny sys_admin/sys_module, /var/lib rwk).

Compose services se etiquetan `apparmor:levlab-web` o `levlab-db`.

## Docker hardening

### `/etc/docker/daemon.json`

```json
{
  "live-restore": true,
  "userns-remap": "default",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3"
  },
  "iptables": true,
  "default-address-pools": [
    { "base": "172.31.0.0/16", "size": 24 }
  ]
}
```

### Seccomp custom

`/etc/docker/seccomp/levlab-default.json` — default `SCMP_ACT_ERRNO`, whitelist ~80 syscalls seguros (accept/bind/connect/read/write/mmap/etc). No `ptrace`, `mount`, `kexec`, `reboot`, `syslog`, `personality`.

### Rootless adicional control-plane

```bash
sudo -iu leviathan bash <<'EOF'
dockerd-rootless-setuptool.sh install
systemctl --user enable docker
docker context create leviathan-rootless --docker host=unix:///run/user/$(id -u)/docker.sock
EOF
```

### Reglas por servicio Compose

Todos los servicios del zoo:

```yaml
security_opt:
  - no-new-privileges:true
  - seccomp:/etc/docker/seccomp/levlab-default.json
  - apparmor:levlab-web
cap_drop:
  - ALL
read_only: true
tmpfs:
  - /tmp:rw,noexec,nosuid,size=128m
pids_limit: 256
```

DBs que necesitan escritura → volúmenes dedicados + AppArmor `levlab-db`.

## Fail2ban + CrowdSec

```ini
# /etc/fail2ban/jail.d/levlab.local
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 4
backend = systemd

[sshd]
enabled = true
```

```bash
cscli collections install crowdsecurity/linux
cscli collections install crowdsecurity/sshd
cscli collections install crowdsecurity/http-cve
systemctl enable --now crowdsec crowdsec-firewall-bouncer
```

## Falco host

```bash
systemctl enable --now falco
```

Tetragon se instala dentro de k3s (no host-wide). Ver [06-observability.md](06-observability.md#runtime-security).

## Kill-switch — implementación real

Plan 1 referenciaba `https://lab.${BASE_DOMAIN}/kill-switch` pero nunca lo wireó. Acá está vivo.

### Componentes

**1. File marker**
`/opt/levlab/KILL_SWITCH` — presencia bloquea todas las acciones del pipeline Leviathan.

**2. Traefik static route**

```yaml
# traefik/dynamic/kill-switch.yml
http:
  routers:
    kill-switch:
      rule: "Host(`lab.${BASE_DOMAIN}`) && PathPrefix(`/kill-switch`)"
      service: kill-switch
      priority: 10000
  services:
    kill-switch:
      loadBalancer:
        servers: []
  middlewares:
    kill-switch-response:
      errors:
        status: ["503"]
        service: kill-switch
```

**3. Middleware Leviathan**

`toolMiddleware.ts` chequea header `X-Kill-Switch: active` o file `/opt/levlab/KILL_SWITCH` **antes** de cada tool call. Ya soportado por ROE schema `kill_switches` — solo lo poblamos correcto.

**4. Operator script `scripts/kill.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
source .env.lab
SERVER_IP="$(cd terraform && terraform output -raw server_ipv4)"
ssh -i "$SSH_PRIVATE_KEY_PATH" -o StrictHostKeyChecking=no leviathan@10.88.0.1 \
  'sudo touch /opt/levlab/KILL_SWITCH && \
   sudo docker compose -f /opt/levlab/docker-compose.yml exec traefik touch /logs/kill-active'
echo "[KILL] marker set. Pipeline aborts on next tool_result."
```

**5. Validación hora 0 (obligatoria)**

`scripts/smoke.sh` confirma:

- `curl -sk https://lab.${BASE_DOMAIN}/kill-switch` → 503 + `X-Kill-Switch: active`
- Leviathan aborta dentro de 1 ciclo tool-result cuando flag levantada
- Flag limpia permite resume

Falla → bloquea kickoff. Fix primero.

## Unattended-upgrades

Instalado + configurado, pero `systemctl mask` durante ventana 24h (evita drift que contamine línea base). Re-enabled por teardown.

## Metadata block post-cloud-init

Bloqueo `169.254.169.254` vía nftables OUTPUT — **después** de cloud-init (sino rompe). Task Ansible `post-cloud-init-metadata-block` aplica la regla una vez `/opt/cloud-init-done` existe.

```nft
chain output {
  ip daddr 169.254.169.254 drop
}
```

Previene SSRF-to-metadata desde contenedores target.
