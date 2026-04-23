"""
tenant-billing-api — deliberately vulnerable multi-tenant FastAPI application
Intentional flaws: tenant_id from path/body without ownership check (horizontal privesc),
invitation flow without token expiry, billing totals readable cross-tenant
"""
import time
from fastapi import FastAPI, Header, HTTPException, Path
from pydantic import BaseModel
import jwt

app = FastAPI(title="TenantBillingAPI", docs_url="/docs")

JWT_SECRET = "lab-tenant-billing-secret-00001"
JWT_ALGO   = "HS256"

# Simulated data store
TENANTS = {
    "t1": {"name": "Acme Corp",    "plan": "enterprise", "balance": 9999.00},
    "t2": {"name": "Small Biz",    "plan": "starter",    "balance":  199.00},
    "t3": {"name": "Hidden Whale", "plan": "enterprise", "balance": 50000.00},
}
INVOICES = {
    "t1": [{"id": "INV-001", "amount": 1200.0, "due": "2026-05-01"}],
    "t2": [{"id": "INV-002", "amount":  49.0,  "due": "2026-05-01"}],
    "t3": [{"id": "INV-003", "amount": 9800.0, "due": "2026-05-01"}],
}
INVITES: dict = {}

class InviteRequest(BaseModel):
    email: str
    tenant_id: str   # Intentional: client supplies target tenant — no ownership check

@app.get("/health")
def health():
    return {"status": "ok", "service": "tenant-billing-api"}

@app.post("/auth/token")
def login(tenant_id: str = "t1", role: str = "user"):
    token = jwt.encode({"sub": f"user@{tenant_id}", "tenant_id": tenant_id,
                        "role": role, "exp": int(time.time()) + 3600},
                       JWT_SECRET, algorithm=JWT_ALGO)
    return {"access_token": token}

def _get_caller(authorization: str = Header(default="")):
    token = authorization.replace("Bearer ", "")
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception:
        return {"tenant_id": "t1", "role": "user"}  # Intentional: unauthenticated defaults to t1

# IDOR: tenant_id in path — no check that caller's token matches requested tenant
@app.get("/tenants/{tenant_id}/billing")
def get_billing(tenant_id: str = Path(...), authorization: str = Header(default="")):
    caller = _get_caller(authorization)
    # Intentional: authorization check is commented out
    # if caller.get("tenant_id") != tenant_id:
    #     raise HTTPException(status_code=403)
    tenant = TENANTS.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404)
    return {"tenant_id": tenant_id, "data": tenant, "invoices": INVOICES.get(tenant_id, [])}

@app.get("/tenants/{tenant_id}/invoices")
def get_invoices(tenant_id: str = Path(...)):
    # Intentional: no auth check at all
    return INVOICES.get(tenant_id, [])

@app.post("/invitations")
def create_invitation(req: InviteRequest, authorization: str = Header(default="")):
    # Intentional: tenant_id from request body — any user can invite to any tenant
    import secrets
    token = secrets.token_hex(4)  # Intentional: short token, predictable
    INVITES[token] = {"email": req.email, "tenant_id": req.tenant_id}
    return {"invite_token": token, "tenant_id": req.tenant_id}

@app.get("/invitations/{token}/accept")
def accept_invitation(token: str):
    invite = INVITES.get(token)
    if not invite:
        raise HTTPException(status_code=404)
    # Intentional: no expiry check, token never invalidated after use
    return {"message": f"Joined tenant {invite['tenant_id']}", "email": invite["email"]}
