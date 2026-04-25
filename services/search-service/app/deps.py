from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from melispy_shared import verify_jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db

AuthorizationHeader = Annotated[str | None, Header()]


@dataclass(frozen=True)
class Principal:
    user_id: str
    org_id: str | None
    claims: dict[str, object]


async def get_current_principal(authorization: AuthorizationHeader = None) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")
    token = authorization.split(" ", 1)[1].strip()
    settings = get_settings()
    try:
        claims = verify_jwt(token, settings.JWT_PUBLIC_KEY_PEM, expected_alg="RS256")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found") from exc
    user_id = str(claims.get("sub", ""))
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")
    org_id_claim = claims.get("org_id")
    org_id = str(org_id_claim) if org_id_claim else None
    return Principal(user_id=user_id, org_id=org_id, claims=claims)


DbSession = Annotated[AsyncSession, Depends(get_db)]
