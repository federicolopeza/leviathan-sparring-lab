from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from melispy_shared import issue_jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crud.tokens import create_magic_link_token, get_valid_magic_link_token, hash_token, new_token
from app.crud.users import get_user_by_email, get_user_by_id
from app.deps.db import get_db
from app.models import Session
from app.models.base import now_utc
from app.schemas.auth import LoginResponse, UserResponse

router = APIRouter(prefix="/v1/auth/magic", tags=["magic"])
logger = structlog.get_logger()
ACCESS_TOKEN_EXPIRES_IN = 900
DbSession = Annotated[AsyncSession, Depends(get_db)]


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkLoginRequest(BaseModel):
    token: str


def _make_access_token(user_id: str, session_id: str, email: str) -> str:
    s = get_settings()
    return issue_jwt(
        {"sub": user_id, "sid": session_id, "email": email},
        s.JWT_PRIVATE_KEY_PEM or "",
        alg="RS256",
        expires_in=ACCESS_TOKEN_EXPIRES_IN,
    )


def _user_response(user: object) -> UserResponse:
    return UserResponse.model_validate({
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "email_verified": user.email_verified,
        "is_admin": user.is_admin,
    })


@router.post("/request")
async def request_magic_link(payload: MagicLinkRequest, db: DbSession) -> dict[str, bool]:
    user = await get_user_by_email(db, str(payload.email))
    if user is not None:
        row, _raw = await create_magic_link_token(db, user.id)
        await db.commit()
        logger.info("magic_link_issued", user_id=user.id, token_id=row.id)
    return {"ok": True}


@router.post("/login", response_model=LoginResponse)
async def magic_link_login(
    payload: MagicLinkLoginRequest,
    request: Request,
    response: Response,
    db: DbSession,
) -> LoginResponse:
    token = await get_valid_magic_link_token(db, payload.token)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")
    user = await get_user_by_id(db, token.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")

    # V-T2-005 INTENTIONAL VULN: token.used_at intentionally NOT set — replayable for 24h TTL
    # token.used_at = now_utc()  # <- omitted by design

    refresh_token = new_token()
    session = Session(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )
    db.add(session)
    await db.flush()
    access_token = _make_access_token(user.id, session.id, user.email)
    await db.commit()

    settings = get_settings()
    response.set_cookie(
        "melispy_session", refresh_token,
        httponly=True, secure=True, samesite="lax",
        domain=settings.COOKIE_DOMAIN,
    )
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRES_IN,
        user=_user_response(user),
    )
