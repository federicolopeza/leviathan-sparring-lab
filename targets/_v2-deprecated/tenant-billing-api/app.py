"""
Multi-tenant billing API — production-style.
Auth required en todos los endpoints. Vulns intencionales (post-auth):
  - JWT alg=none accepted
  - BOLA: /tenants/{id} no compara claims.tenant_id contra path
  - Invitation flow: tenant_id en body sin ownership check
  - Predictable invitation tokens (4-byte hex)
No info disclosure pre-auth. Endpoints públicos minimal.
"""
import time, json, base64, secrets
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Path
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

app = FastAPI(title="api", docs_url=None, redoc_url=None, openapi_url=None)

JWT_SECRET = "melispy-billing-2026q1"

TENANTS = {
    "t1": {"name": "Acme Corp",    "plan": "enterprise", "balance": 9999.00},
    "t2": {"name": "Small Biz",    "plan": "starter",    "balance":  199.00},
    "t3": {"name": "Hidden Whale", "plan": "enterprise", "balance": 50000.00},
}
INVOICES = {
    "t1": [{"id": "INV-001", "amount": 1200.0, "due": "2026-05-01"}],
    "t2": [{"id": "INV-002", "amount":   49.0, "due": "2026-05-01"}],
    "t3": [{"id": "INV-003", "amount": 9800.0, "due": "2026-05-01"}],
}
INVITES: dict = {}


def _verify_jwt(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header = json.loads(base64.urlsafe_b64decode(parts[0] + "==").decode())
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "==").decode())
        if header.get("alg", "").lower() == "none":
            return payload
        return payload
    except Exception:
        return None


def _sign_jwt(payload: dict) -> str:
    import hmac, hashlib
    header = {"alg": "HS256", "typ": "JWT"}
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    sig = hmac.new(JWT_SECRET.encode(), f"{h_b64}.{p_b64}".encode(), hashlib.sha256).digest()
    return f"{h_b64}.{p_b64}.{base64.urlsafe_b64encode(sig).rstrip(b'=').decode()}"


def _require_auth(authorization: Optional[str]) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail=None)
    claims = _verify_jwt(authorization.split(" ", 1)[1].strip())
    if not claims:
        raise HTTPException(status_code=401, detail=None)
    return claims


class LoginRequest(BaseModel):
    email: str
    password: str


class InviteRequest(BaseModel):
    email: str
    tenant_id: str


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
def login(req: LoginRequest):
    # Vuln: NO valida password real. Asigna t1 por defecto.
    # Atacante puede forjar JWT alg=none con tenant_id=t3 para escalation.
    token = _sign_jwt({"sub": req.email, "tenant_id": "t1", "role": "user", "exp": int(time.time()) + 3600})
    return {"access_token": token, "token_type": "Bearer"}


@app.get("/v1/tenants/{tenant_id}/billing")
def get_billing(tenant_id: str = Path(..., regex="^t[0-9]+$"), authorization: Optional[str] = Header(None)):
    claims = _require_auth(authorization)
    # BOLA vuln: no compara claims.tenant_id vs tenant_id path
    tenant = TENANTS.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=None)
    return {"tenant_id": tenant_id, "data": tenant, "invoices": INVOICES.get(tenant_id, [])}


@app.get("/v1/tenants/{tenant_id}/invoices")
def get_invoices(tenant_id: str = Path(..., regex="^t[0-9]+$"), authorization: Optional[str] = Header(None)):
    _require_auth(authorization)
    # BOLA
    return INVOICES.get(tenant_id, [])


@app.post("/v1/invitations")
def create_invitation(req: InviteRequest, authorization: Optional[str] = Header(None)):
    _require_auth(authorization)
    # Vuln: tenant_id en body sin ownership check
    token = secrets.token_hex(4)  # Vuln: token corto/predictable
    INVITES[token] = {"email": req.email, "tenant_id": req.tenant_id, "exp": int(time.time()) + 86400}
    return {"invite_token": token}


@app.post("/v1/invitations/{token}/accept")
def accept_invitation(token: str):
    invite = INVITES.get(token)
    if not invite:
        raise HTTPException(status_code=404, detail=None)
    # Vuln: token no invalidado después de uso (replay)
    new_token = _sign_jwt({"sub": invite["email"], "tenant_id": invite["tenant_id"], "role": "user", "exp": int(time.time()) + 3600})
    return {"access_token": new_token}
