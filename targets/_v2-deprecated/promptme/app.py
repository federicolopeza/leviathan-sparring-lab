"""
LLM proxy — production-style. Auth required.
Vulns intencionales post-auth:
  - JWT alg=none accepted
  - system_override aceptado si caller parece "interno" (X-Forwarded-For trust → spoofable)
  - prompt injection via concat
"""
import os, json, base64
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

app = FastAPI(title="api", docs_url=None, redoc_url=None, openapi_url=None)

SYSTEM_PROMPT = "Helpful assistant for Melispy customers."
INTERNAL_DATA = {"model_version": "v1", "knowledge_cutoff": "2026-04-01"}


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


def _is_internal(xff: Optional[str], peer: Optional[str]) -> bool:
    candidate = (xff or peer or "").split(",")[0].strip()
    return candidate.startswith(("10.", "172.30.", "127.")) or candidate == "::1"


class ChatRequest(BaseModel):
    message: str
    system_override: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(status_code=404, content={"error": "not_found"})


@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc):
    return JSONResponse(status_code=400, content={"error": "bad_request"})


@app.post("/v1/chat/completions")
async def chat(
    req: ChatRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
    x_forwarded_for: Optional[str] = Header(None),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail=None)
    if not _verify_jwt(authorization.split(" ", 1)[1].strip()):
        raise HTTPException(status_code=401, detail=None)

    effective = SYSTEM_PROMPT
    if req.system_override and _is_internal(x_forwarded_for, request.client.host if request.client else None):
        effective = req.system_override

    response = "I am a helpful assistant. How can I help?"
    if req.system_override and _is_internal(x_forwarded_for, request.client.host if request.client else None):
        msg_lower = req.message.lower()
        if "system" in msg_lower or "ignore" in msg_lower:
            response = f"Effective system: {effective}"

    return {"response": response, "model": INTERNAL_DATA["model_version"]}
