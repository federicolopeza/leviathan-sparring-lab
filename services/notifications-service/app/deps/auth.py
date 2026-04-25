from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, HTTPException, status
from melispy_shared import verify_jwt

from app.config import get_settings

AuthorizationHeader = Annotated[str | None, Header()]


@dataclass(frozen=True)
class Principal:
    user_id: str
    org_id: str
    claims: dict[str, object]

    @property
    def is_admin(self) -> bool:
        user_claim = self.claims.get("user")
        if isinstance(user_claim, dict):
            return bool(user_claim.get("is_admin"))
        return bool(self.claims.get("is_admin"))

    @property
    def is_service_token(self) -> bool:
        return self.claims.get("token_type") in {"service", "service-token"} or bool(
            self.claims.get("service_token")
        )


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
    org_id = str(claims.get("org_id") or f"org-{user_id}")
    return Principal(user_id=user_id, org_id=org_id, claims=claims)


async def require_admin_or_service(principal: Principal) -> Principal:
    if not principal.is_admin and not principal.is_service_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not Found")
    return principal
