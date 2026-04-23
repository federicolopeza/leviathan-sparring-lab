# 13 — Credentials guide (cómo obtener + dónde guardar)

Esta guía documenta **cómo** conseguir cada credencial. **NUNCA** commitear valores reales — solo plantillas.

## Regla de oro

- `.env.lab` → valores reales → **gitignored** (nunca committed)
- `.env.lab.example` → placeholders → committed
- Este archivo → cómo conseguir cada valor → committed
- Operator tiene su copia local privada de `.env.lab` con valores reales

## Storage local — operador

Tres niveles:

1. **`.env.lab`** (gitignored en repo) → todos los secrets del lab
2. **Password manager** (1Password / Bitwarden / KeePassXC) → backup de tokens con rotation dates
3. **Physical memory** — solo passwords master, nada más

NO guardar tokens en:
- Chat logs
- Notas en texto plano no-encriptadas
- Screenshots
- Cloud sync sin cifrar (Drive/Dropbox raw)

## Credencial por credencial

### 1. `SSH_PRIVATE_KEY_PATH`

Path absoluto a tu key privada ED25519 que matchea la pubkey cargada en Vultr SSH Keys registry.

**Qué hacer:** ya existe en tu laptop. Path:

```
SSH_PRIVATE_KEY_PATH=C:/Users/Lopez/.ssh/id_ed25519_digitalocean
```

Fingerprint (para verify): `SHA256:6tBY+EKZHrPkN4pP0UslzAkOBQYp55NYukxt+XAP9no`

**Rotation:** generar nueva cada 90 días (opcional para uso personal).

### 2. `VULTR_API_KEY` — **NO usado en esta corrida**

Scaffold lo hace opcional. Operator destroys manual vía UI post-benchmark.

Si más adelante querés teardown programático:

- Link: https://my.vultr.com/settings/#settingsapi
- Account → Settings → API → Personal Access Tokens → **Add New Token**
- Name: `leviathan-sparring-lab`
- Permissions: **Manage All** o más granular
- Copy token → guardar en password manager

### 3. `VULTR_VPS_IP`

Public IPv4 de la VPS. Visible en Vultr dashboard → instance detail.

Corrida actual: `140.82.60.135`

### 4. Cloudflare credentials — el paquete crítico

#### 4a. Cuenta Cloudflare

Link signup: https://dash.cloudflare.com/sign-up

- Free plan — suficiente para:
  - DNS
  - Managed Rules (WAF)
  - OWASP CRS
  - IP Access Rules / Custom Rules
  - Tunnel (cloudflared)
- 2FA **obligatorio** — activar via dashboard → My Profile → Authentication

#### 4b. Migrar dominio a Cloudflare (si aplica)

Procedimiento completo ver [sección abajo § Migración DNS a Cloudflare](#migración-dns-a-cloudflare).

#### 4c. `CF_ZONE_ID`

Dashboard → click dominio → scroll down panel derecho "API". Campo `Zone ID`, botón copy.

32 hex chars.

#### 4d. `CF_ACCOUNT_ID`

Mismo panel que Zone ID. Campo `Account ID`.

32 hex chars.

#### 4e. `CF_API_TOKEN`

Link: https://dash.cloudflare.com/profile/api-tokens

1. **Create Token** → **Custom Token** → Get started
2. Name: `leviathan-sparring-lab`
3. Permissions (agregar 5):
   | Scope | Permission | Access |
   |---|---|---|
   | Zone | Zone | Read |
   | Zone | DNS | Edit |
   | Zone | Zone WAF | Edit |
   | Account | Rulesets | Edit |
   | Account | Cloudflare Tunnel | Edit |
4. **Zone Resources** → Include → Specific zone → el dominio elegido
5. **Account Resources** → Include → All accounts
6. TTL: forever (revocable)
7. Continue to summary → **Create Token**
8. **COPIA YA** — aparece una sola vez. Guardar en password manager.

**Rotation:** cada 90 días. Revocar + recrear via dashboard.

#### 4f. `CF_TUNNEL_ID` + `CF_TUNNEL_TOKEN`

Se generan al crear el tunnel (se hace en bootstrap — Terraform + `cloudflared tunnel create`).

No se setean manualmente. Terraform escribe en `.env.lab` al final del apply.

### 5. `WireGuard keys`

Se generan **automático** por `scripts/generate-wg-keys.sh` en preflight. Operator solo provee su pubkey laptop (via el comando abajo).

#### Generar pubkey laptop

En tu laptop Windows (git bash):

```bash
wg genkey | tee ~/.ssh/wg-laptop-private.key | wg pubkey > ~/.ssh/wg-laptop-public.key
cat ~/.ssh/wg-laptop-public.key
```

Pubkey → `WG_CLIENT_PUBLIC_KEY` en `.env.lab`.
Privada laptop → `~/.ssh/wg-laptop-private.key`, usada por `wg0.conf` local cuando te conectes.

**Rotation:** por corrida (scaffold rota en `scripts/teardown.sh --rotate`).

### 6. Credenciales internas generadas

Scaffold genera + setea automático:

- `GRAFANA_ADMIN_PASSWORD` → random 24-char alfanum, escrito en `.env.lab`
- `WAZUH_API_PASSWORD` → random 24-char
- `MINIO_ROOT_USER=minioadmin` (fijo, no secreto)
- `MINIO_ROOT_PASSWORD` → random 24-char
- `VAULT_DEV_ROOT_TOKEN_ID` → random 24-char

Visible en `.env.lab` local después de bootstrap. Nunca committed.

### 7. `RUN_ID`

Identificador único por corrida. Default `YYYYMMDD-aN` (ej `20260423-a1`).

Setearlo en `.env.lab` antes de bootstrap.

## Migración DNS a Cloudflare

Aplica a melispy.com (DO DNS → CF) para esta corrida.

### Prerequisitos

- Dominio registrado en Namecheap (o registrar similar con control de nameservers)
- Dominio no tiene servicios críticos (email, web apex) activos
- Cuenta CF activa + verificada

### Pasos

1. **CF dashboard** → https://dash.cloudflare.com/add-site
2. Enter site: `melispy.com`
3. Plan: **Free**
4. CF escanea records DO → importa automático
5. Review records (si el dominio estaba limpio, casi vacío)
6. CF muestra 2 nameservers únicos:
   ```
   <nombre1>.ns.cloudflare.com
   <nombre2>.ns.cloudflare.com
   ```
7. En **Namecheap** → https://ap.www.namecheap.com/domains/list/ → Manage → Nameservers
8. Cambiar a **Custom DNS**, reemplazar los 3 de DigitalOcean con los 2 de CF
9. Save (✓ verde)
10. En CF dashboard → botón "Check nameservers" para forzar verify
11. Esperar status **Active** (5 min - 1 hora típico)
12. Una vez active → Zone ID + Account ID disponibles (paso 4c/4d arriba)

### Verify propagación

En git bash:

```bash
dig NS melispy.com +short
```

Debe mostrar `*.ns.cloudflare.com`, no `digitalocean.com`.

Si sigue DO → esperar más o verificar config Namecheap.

### Rollback

Si algo sale mal:

1. Namecheap → Nameservers → cambiar back a `ns1.digitalocean.com`, `ns2.digitalocean.com`, `ns3.digitalocean.com`
2. Esperar propagación
3. Dominio vuelve a DO DNS

Sin downtime si el dominio no tenía servicios vivos.

## `.env.lab` — template final

Después de conseguir todo:

```bash
# === Cloudflare ===
BASE_DOMAIN=melispy.com
CF_API_TOKEN=<del paso 4e>
CF_ZONE_ID=<del paso 4c>
CF_ACCOUNT_ID=<del paso 4d>
CF_TUNNEL_ID=               # vacío — Terraform lo genera
CF_TUNNEL_TOKEN=            # vacío — Terraform lo genera

# === Vultr ===
VULTR_API_KEY=              # opcional — skip this run
VULTR_VPS_IP=140.82.60.135
VULTR_REGION=ewr
VULTR_PLAN=vx1-g-8c-32g-480s

# === SSH ===
OPERATOR_PUBLIC_IP=         # auto-detect via scripts
SSH_PUBLIC_KEY_PATH=C:/Users/Lopez/.ssh/id_ed25519_digitalocean.pub
SSH_PRIVATE_KEY_PATH=C:/Users/Lopez/.ssh/id_ed25519_digitalocean

# === WireGuard ===
WG_SERVER_PRIVATE_KEY=      # auto-generated by preflight
WG_SERVER_PUBLIC_KEY=       # auto-generated by preflight
WG_CLIENT_PUBLIC_KEY=<del § 5 arriba>
WG_CLIENT_ADDRESS=10.88.0.2/32

# === DNS resolvers ===
DNS_RESOLVER_1=1.1.1.1
DNS_RESOLVER_2=9.9.9.9

# === Observability ===
RUN_ID=20260423-a1
GRAFANA_ADMIN_PASSWORD=     # auto-generated
WAZUH_API_PASSWORD=         # auto-generated
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=        # auto-generated
VAULT_DEV_ROOT_TOKEN_ID=    # auto-generated

# === Bandwidth guard ===
VNSTAT_SOFT_CAP_GB=2000
```

Archivo final en `C:\Users\Lopez\OneDrive\Escritorio\Proyectos\leviathan-sparring-lab\.env.lab`.

## Rotation policy

| Credencial | Frecuencia | Método |
|---|---|---|
| CF_API_TOKEN | 90 días | Dashboard → revocar + recrear |
| SSH key ED25519 | 90 días | `ssh-keygen -t ed25519` + update Vultr SSH Keys |
| WG keys | Por corrida | `scripts/generate-wg-keys.sh --rotate` |
| Grafana/Wazuh/MinIO/Vault passwords | Por corrida | Auto-regenerated en bootstrap |
| VULTR_API_KEY | 90 días si usado | Dashboard |

## Revocación de emergencia

Si creés que cualquier credencial leaked:

1. **CF token**: https://dash.cloudflare.com/profile/api-tokens → Revoke inmediato
2. **SSH key**: remover pubkey de Vultr SSH Keys + `passwd -l root` en VPS + rotar
3. **Vultr API key**: https://my.vultr.com/settings/#settingsapi → Revoke
4. **WG keys**: levantar kill-switch + `scripts/teardown.sh` + generar nuevas
5. **Domain hijack**: Namecheap → cambiar password + 2FA + contactar support

## Checklist final antes de bootstrap

```
[ ] .env.lab existe en repo root
[ ] .env.lab NO está en git status (.gitignore funciona)
[ ] SSH key fingerprint verifica
[ ] CF token funciona: curl -H "Authorization: Bearer $CF_API_TOKEN" \
      https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID | jq '.success'
    (debe devolver true)
[ ] CF zone active (no "pending nameserver update")
[ ] dig NS melispy.com → muestra cloudflare.com
[ ] SSH to root@VPS_IP funciona
[ ] WG client pubkey generada + guardada
[ ] 2FA activo en cuentas CF + Namecheap + Vultr
```

Cuando todo check → `./scripts/bootstrap.sh`.
