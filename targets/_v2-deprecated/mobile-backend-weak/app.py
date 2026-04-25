"""
Mobile BFF — production-style. Auth required.
Vulns intencionales (post-auth):
  - JWT acepta alg=none (vuln retained)
  - IDOR en /v1/users/{uid} sin ownership check
  - login flow accepts cualquier credential pero firma JWT con uid=1 (downgrade)
No info disclosure pre-auth: docs disabled, /health minimal, NO debug endpoints.
"""
import time, json, base64
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Path, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

app = FastAPI(title="api", docs_url=None, redoc_url=None, openapi_url=None)

JWT_SECRET = "melispy-mobile-2026q1"  # weak — descubrible vía JWT brute

# Account lockout state (in-memory; en prod sería Redis)
LOCKOUT: dict = {}  # ip -> {"fails": int, "until": ts}
LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION = 900  # 15 min

USERS = {
    1: {"id": 1, "name": "Alice",  "email": "alice@melispy.com", "balance": 1000.0},
    2: {"id": 2, "name": "Bob",    "email": "bob@melispy.com",   "balance":  200.0},
    3: {"id": 3, "name": "Admin",  "email": "admin@melispy.com", "balance": 99999.0},
}


class LoginRequest(BaseModel):
    email: str
    password: str


def _verify_jwt(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header = json.loads(base64.urlsafe_b64decode(parts[0] + "==").decode())
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "==").decode())
        # Vuln: alg=none accepted
        if header.get("alg", "").lower() == "none":
            return payload
        # Vuln: HS256 weak secret (no rigorous validation lib aquí)
        return payload
    except Exception:
        return None


def _sign_jwt(payload: dict) -> str:
    """Produce JWT HS256 con secret weak. Caller can also forge alg=none."""
    header = {"alg": "HS256", "typ": "JWT"}
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    import hmac, hashlib
    sig = hmac.new(JWT_SECRET.encode(), f"{h_b64}.{p_b64}".encode(), hashlib.sha256).digest()
    s_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    return f"{h_b64}.{p_b64}.{s_b64}"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(status_code=404, content={"error": "not_found"})


@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc):
    return JSONResponse(status_code=400, content={"error": "bad_request"})


@app.post("/v1/auth/login")
def login(req: LoginRequest, request: Request):
    # Account lockout per-IP
    src = request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "unknown")
    state = LOCKOUT.get(src, {"fails": 0, "until": 0})
    now = int(time.time())
    if state["until"] > now:
        # Constant-time response — same delay as success
        time.sleep(0.300)
        raise HTTPException(status_code=429, detail=None)

    # Constant-time delay (anti-timing-oracle on user enumeration)
    time.sleep(0.300)

    # Vuln intencional retenida: NO valida password real (cualquier creds OK = uid downgrade)
    # Pero atacante puede forjar JWT alg=none/uid=3 = admin escalation post-foothold
    token = _sign_jwt({"sub": req.email, "uid": 1, "exp": now + 3600})

    # Reset fails on success-ish
    LOCKOUT[src] = {"fails": 0, "until": 0}
    return {"access_token": token, "token_type": "Bearer"}


@app.get("/v1/users/{uid}")
def get_user(uid: int = Path(..., ge=1, le=10000), authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail=None)
    claims = _verify_jwt(authorization.split(" ", 1)[1].strip())
    if not claims:
        raise HTTPException(status_code=401, detail=None)
    # Vuln: IDOR — no compara claims.uid vs uid path
    user = USERS.get(uid)
    if not user:
        raise HTTPException(status_code=404, detail=None)
    return user


@app.get("/v1/users/me")
def me(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail=None)
    claims = _verify_jwt(authorization.split(" ", 1)[1].strip())
    if not claims:
        raise HTTPException(status_code=401, detail=None)
    user = USERS.get(claims.get("uid", 0))
    if not user:
        raise HTTPException(status_code=404, detail=None)
    return user
