"""
DVAIA — production-style AI agent service.
Auth required. Vulns intencionales internas (post-auth):
  - JWT validates with weak HS256 secret + accepts alg=none
  - tool_call dispatch sin validation post-auth
  - prompt injection via concat
No info disclosure pre-auth: docs disabled, error pages genéricas, /health minimal.
"""
import subprocess, os, json, base64
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

# Disable docs/redoc/openapi en prod
app = FastAPI(
    title="api",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

JWT_SECRET = os.environ.get("JWT_SECRET", "melispy-jwt-2026q1")  # weak secret — intentional
INTERNAL_FLAG = "LEVIATHAN{dvaia_post_auth_tool_rce}"  # solo accesible post-explotación

# Genéricos: NO leak en respuesta
GENERIC_ERROR = {"error": "invalid_request"}


def _verify_jwt(token: str) -> Optional[dict]:
    """Constant-time JWT verify. Vuln intencional retenida: acepta alg=none + HS256 weak."""
    import hmac, hashlib, time
    t0 = time.perf_counter()
    result = None
    try:
        parts = token.split(".")
        if len(parts) == 3:
            header = json.loads(base64.urlsafe_b64decode(parts[0] + "==").decode())
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + "==").decode())
            # Vuln 1: alg=none accepted (post-auth, gonxa needs to find this)
            if header.get("alg", "").lower() == "none":
                result = payload
            # Vuln 2: HS256 weak secret — sig validation HMAC-CT
            elif header.get("alg") == "HS256":
                expected = hmac.new(
                    JWT_SECRET.encode(),
                    f"{parts[0]}.{parts[1]}".encode(),
                    hashlib.sha256,
                ).digest()
                actual = base64.urlsafe_b64decode(parts[2] + "==")
                if hmac.compare_digest(expected, actual):
                    result = payload
    except Exception:
        result = None
    # Constant-time padding: guarantee >= 50ms response
    elapsed = time.perf_counter() - t0
    if elapsed < 0.050:
        time.sleep(0.050 - elapsed)
    return result


def _read_file(path: str) -> str:
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return str(e)


def _write_file(path: str, content: str) -> str:
    try:
        if os.path.dirname(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"ok:{len(content)}"
    except Exception as e:
        return str(e)


def _exec_shell(cmd: str) -> str:
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)


TOOLS = {"read_file": _read_file, "write_file": _write_file, "exec_shell": _exec_shell}


class AgentRequest(BaseModel):
    message: str
    tool_call: Optional[dict] = None


@app.get("/health")
def health():
    return {"status": "ok"}


# Catchall: 404 plain (sin revelar paths existentes)
@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(status_code=404, content={"error": "not_found"})


@app.exception_handler(500)
async def server_error(request, exc):
    return JSONResponse(status_code=500, content={"error": "internal"})


@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc):
    # Generic 400 — no leak field-level errors
    return JSONResponse(status_code=400, content={"error": "bad_request"})


@app.post("/v1/chat")
def chat(req: AgentRequest, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail=None)
    token = authorization.split(" ", 1)[1].strip()
    claims = _verify_jwt(token)
    if not claims:
        raise HTTPException(status_code=401, detail=None)

    # POST-AUTH: tool_call vuln retained, prompt injection retained
    tool_result = None
    if req.tool_call:
        name = req.tool_call.get("name", "")
        args = req.tool_call.get("args", {})
        fn = TOOLS.get(name)
        if fn:
            try:
                tool_result = fn(**args) if isinstance(args, dict) else None
            except Exception as e:
                tool_result = str(e)

    # Prompt injection vuln: concat sin sanitize, response includes raw user msg
    response = f"Acknowledged: {req.message[:200]}"

    # Flag access: sólo si el atacante usa exec_shell para leer env
    return {"response": response, "tool_result": tool_result}
