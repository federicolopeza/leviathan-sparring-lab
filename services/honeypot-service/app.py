"""
Honeypot — catches scanner probes for common attack paths.
Returns plausible fake responses to waste attacker time + logs heavily.
EVERY hit logged at WARNING level → ingested by Promtail → Loki.

Design:
  - All known attack paths return realistic but useless data
  - Random delay 100-800ms per hit (tarpit, anti-fingerprint)
  - Includes attack-pattern detection logging
  - NO real auth — just fake plausibility
"""
import json, time, random, hashlib, logging
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse, Response

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"honeypot","msg":%(message)s}',
)
log = logging.getLogger("honeypot")

app = FastAPI(title="api", docs_url=None, redoc_url=None, openapi_url=None)


def _trace_id(request: Request) -> str:
    """Generate trace ID per request (sticky per-IP for correlation)."""
    src = (request.headers.get("cf-connecting-ip") or
           request.client.host if request.client else "unknown")
    ua = request.headers.get("user-agent", "")
    h = hashlib.sha256(f"{src}:{ua}:{int(time.time()/3600)}".encode()).hexdigest()[:12]
    return h


async def _track(request: Request, category: str, path_hit: str, severity: str = "warning"):
    """Log honeypot interaction with full attacker context."""
    src = request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "unknown")
    body = ""
    try:
        body = (await request.body())[:200].decode(errors="replace")
    except Exception:
        pass
    payload = json.dumps({
        "trace": _trace_id(request),
        "src":   src,
        "ua":    request.headers.get("user-agent", ""),
        "ja3":   request.headers.get("cf-bot-management-ja3", ""),
        "path":  path_hit,
        "method": request.method,
        "host":  request.headers.get("host", ""),
        "ref":   request.headers.get("referer", ""),
        "body_pfx": body,
        "category": category,
        "severity": severity,
        "asn":   request.headers.get("cf-ipcountry", "") + "/" + request.headers.get("cf-ray", ""),
    })
    log.warning(payload)
    # Tarpit: random delay 100-800ms
    time.sleep(random.uniform(0.1, 0.8))


# ─── Common scanner / recon probes ────────────────────────────────────

@app.get("/.env")
@app.get("/.env.local")
@app.get("/.env.production")
async def env_probe(request: Request):
    await _track(request, "secrets-recon", request.url.path, "high")
    # Plausible but useless
    return PlainTextResponse(
        "NODE_ENV=production\n"
        "API_VERSION=v3.2\n"
        "BUILD_DATE=2026-04-25\n"
    )


@app.get("/.git/HEAD")
async def git_head(request: Request):
    await _track(request, "git-leak", request.url.path, "high")
    return PlainTextResponse("ref: refs/heads/main\n")


@app.get("/.git/config")
async def git_config(request: Request):
    await _track(request, "git-leak", request.url.path, "high")
    return PlainTextResponse(
        "[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n"
        "[remote \"origin\"]\n\turl = git@github.com:melispy/internal.git\n"
    )


@app.get("/.aws/credentials")
@app.get("/.aws/config")
async def aws_credentials(request: Request):
    await _track(request, "aws-recon", request.url.path, "critical")
    raise HTTPException(status_code=404, detail=None)


@app.get("/admin")
@app.get("/admin/")
@app.get("/admin/login")
@app.get("/administrator")
async def admin_panel(request: Request):
    await _track(request, "admin-probe", request.url.path, "warning")
    return HTMLResponse(
        '<!DOCTYPE html><html><head><title>Admin</title></head>'
        '<body><h2>Restricted</h2><form method="POST" action="/admin/login">'
        '<input name="username" type="text" placeholder="Username"/>'
        '<input name="password" type="password" placeholder="Password"/>'
        '<button>Sign in</button></form></body></html>'
    )


@app.post("/admin/login")
async def admin_login_post(request: Request):
    await _track(request, "admin-bruteforce", "/admin/login", "high")
    # Constant 401 — no oracle leak between valid/invalid users
    time.sleep(random.uniform(0.5, 1.5))  # extra tarpit
    return JSONResponse(status_code=401, content={"error": "invalid_credentials"})


@app.get("/wp-admin")
@app.get("/wp-admin/")
@app.get("/wp-login.php")
@app.get("/xmlrpc.php")
async def wordpress_probe(request: Request):
    await _track(request, "wordpress-recon", request.url.path, "warning")
    raise HTTPException(status_code=404, detail=None)


@app.get("/phpmyadmin")
@app.get("/phpmyadmin/")
@app.get("/pma/")
@app.get("/pma/index.php")
async def phpmyadmin_probe(request: Request):
    await _track(request, "phpmyadmin-recon", request.url.path, "warning")
    raise HTTPException(status_code=404, detail=None)


@app.get("/actuator")
@app.get("/actuator/")
@app.get("/actuator/health")
@app.get("/actuator/env")
@app.get("/actuator/info")
@app.get("/actuator/metrics")
@app.get("/actuator/heapdump")
async def actuator_probe(request: Request):
    """Spring Boot actuator probes — typical recon."""
    await _track(request, "spring-actuator", request.url.path, "high")
    if request.url.path == "/actuator/health":
        return {"status": "UP"}
    raise HTTPException(status_code=404, detail=None)


@app.get("/console")
@app.get("/console/login")
@app.get("/manager/html")
@app.get("/manager/text/list")
async def jee_console(request: Request):
    """Tomcat / WebLogic / JBoss admin probes."""
    await _track(request, "jee-console-probe", request.url.path, "warning")
    raise HTTPException(status_code=404, detail=None)


@app.get("/server-status")
@app.get("/server-info")
async def apache_status(request: Request):
    await _track(request, "apache-status-probe", request.url.path, "warning")
    raise HTTPException(status_code=404, detail=None)


@app.get("/api/v1/admin/users")
@app.get("/api/v1/admin/config")
@app.get("/api/internal/users")
@app.get("/v1/internal/customers")
async def fake_api_admin(request: Request):
    """Plausible API admin probes — return realistic 401."""
    await _track(request, "api-admin-probe", request.url.path, "high")
    return JSONResponse(
        status_code=401,
        content={"error": "Unauthorized", "code": "AUTH_REQUIRED"},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.get("/.well-known/internal-keys")
@app.get("/.well-known/openid-configuration")
async def wellknown(request: Request):
    if request.url.path == "/.well-known/openid-configuration":
        # Plausible: return realistic OIDC discovery (issuer that is itself decoy)
        await _track(request, "oidc-discovery", request.url.path, "info")
        return {
            "issuer": "https://melispy.com",
            "authorization_endpoint": "https://melispy.com/oauth/authorize",
            "token_endpoint": "https://melispy.com/oauth/token",
            "jwks_uri": "https://melispy.com/.well-known/jwks.json",
        }
    await _track(request, "wellknown-probe", request.url.path, "high")
    raise HTTPException(status_code=404, detail=None)


@app.get("/.well-known/jwks.json")
async def jwks(request: Request):
    await _track(request, "jwks-probe", request.url.path, "info")
    # Decoy JWKS — no usable keys, just structure
    return {
        "keys": [{
            "kty": "RSA",
            "kid": "decoy-2026",
            "use": "sig",
            "alg": "RS256",
            "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
            "e": "AQAB"
        }]
    }


@app.get("/oauth/authorize")
async def fake_oauth_authorize(request: Request):
    await _track(request, "oauth-probe", request.url.path, "warning")
    return HTMLResponse(
        '<!DOCTYPE html><html><body>'
        '<h2>Sign in to Melispy</h2>'
        '<form method="POST" action="/oauth/login">'
        '<input name="email" placeholder="Email"/>'
        '<input name="password" type="password" placeholder="Password"/>'
        '<button>Sign in</button></form></body></html>'
    )


@app.post("/oauth/token")
async def fake_oauth_token(request: Request):
    await _track(request, "oauth-token-attempt", request.url.path, "high")
    return JSONResponse(status_code=400, content={"error": "invalid_grant"})


@app.get("/swagger.json")
@app.get("/swagger-ui")
@app.get("/api-docs")
@app.get("/openapi.yaml")
@app.get("/redoc.html")
async def docs_probe(request: Request):
    await _track(request, "docs-probe", request.url.path, "warning")
    raise HTTPException(status_code=404, detail=None)


@app.get("/login.action")
async def struts_probe(request: Request):
    """Struts CVE-2017-5638 + similar."""
    await _track(request, "struts-probe", request.url.path, "high")
    raise HTTPException(status_code=404, detail=None)


@app.get("/_next/static/{path:path}")
async def nextjs_static_probe(request: Request, path: str):
    """Next.js _next/static probes — recon for app structure."""
    await _track(request, "nextjs-recon", request.url.path, "info")
    raise HTTPException(status_code=404, detail=None)


# ─── Catchall (unknown paths) ─────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(404)
async def not_found(request, exc):
    # Track unknown-path access from honeypot (signal: scanning)
    try:
        await _track(request, "unknown-path", request.url.path, "info")
    except Exception:
        pass
    return JSONResponse(status_code=404, content={"error": "not_found"})
