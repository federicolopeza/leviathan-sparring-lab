from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status
from jwt import InvalidTokenError
from melispy_shared import legacy_verify
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/legacy/auth", tags=["legacy"])
UserAgentHeader = Annotated[str | None, Header()]


class LegacyVerifyRequest(BaseModel):
    token: str = Field(min_length=1)


@router.post("/verify")  # V-T2-004 INTENTIONAL VULN ENTRY POINT
async def verify_legacy_token(
    payload: LegacyVerifyRequest,
    user_agent: UserAgentHeader = None,
) -> dict[str, str]:
    if "MelispyMobile/" not in (user_agent or ""):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    try:
        claims = legacy_verify(payload.token)  # V-T2-004 INTENTIONAL VULN: alg=none legacy verify
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found") from exc
    user_id = str(claims.get("user_id") or claims.get("sub") or "")
    email = str(claims.get("email") or "")
    if not user_id or not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")
    return {"user_id": user_id, "email": email}
