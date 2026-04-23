"""
mobile-backend-weak — deliberately vulnerable FastAPI mobile backend
Intentional flaws: hardcoded API keys in responses, weak JWT (alg=none accepted),
IDOR on /user/<id>, no rate limiting, debug endpoints
"""
import time
from fastapi import FastAPI, Header, Path, HTTPException
from pydantic import BaseModel
import jwt

app = FastAPI(title="MobileBackend", docs_url="/docs")

# Intentional: hardcoded credentials and keys
HARDCODED_API_KEY = "mob-api-key-lab-000000000000001"
JWT_SECRET        = "mobile-jwt-secret-lab-0000001"
JWT_ALGORITHMS    = ["HS256", "none"]  # Intentional: alg=none accepted

USERS = {
    1: {"id": 1, "name": "Alice",  "email": "alice@lab.local", "phone": "+1-555-0001", "balance": 1000.0},
    2: {"id": 2, "name": "Bob",    "email": "bob@lab.local",   "phone": "+1-555-0002", "balance":  200.0},
    3: {"id": 3, "name": "Admin",  "email": "admin@lab.local", "phone": "+1-555-0003", "balance": 99999.0},
}

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/health")
def health():
    # Intentional: leaks API key in health response
    return {"status": "ok", "service": "mobile-backend", "debug_api_key": HARDCODED_API_KEY}

@app.post("/auth/login")
def login(req: LoginRequest):
    # Intentional: accepts any credentials
    uid = 1 if req.username != "admin" else 3
    token = jwt.encode({"sub": req.username, "uid": uid, "exp": int(time.time()) + 3600},
                       JWT_SECRET, algorithm="HS256")
    return {"access_token": token, "hardcoded_key": HARDCODED_API_KEY}

@app.get("/user/{uid}")
def get_user(uid: int = Path(...), authorization: str = Header(default="")):
    # Intentional: no ownership check — IDOR (any token can read any user)
    token = authorization.replace("Bearer ", "")
    try:
        jwt.decode(token, JWT_SECRET, algorithms=JWT_ALGORITHMS)
    except Exception:
        pass  # Intentional: auth failure silently allowed
    user = USERS.get(uid)
    if not user:
        raise HTTPException(status_code=404)
    return user

@app.get("/admin/users")
def admin_users(x_api_key: str = Header(default="")):
    # Intentional: hardcoded key check, key also leaked in /health
    if x_api_key != HARDCODED_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid key")
    return list(USERS.values())

@app.get("/debug/config")
def debug_config():
    # Intentional: no auth — exposes all secrets
    return {"jwt_secret": JWT_SECRET, "api_key": HARDCODED_API_KEY, "users": USERS}
