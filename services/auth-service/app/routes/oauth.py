from __future__ import annotations

import secrets
from typing import Annotated

import jwt
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from melispy_shared import issue_jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crud.tokens import hash_token, new_token
from app.crud.users import create_user, get_user_by_email, get_user_by_id
from app.deps.db import get_db
from app.models import Session
from app.models.base import now_utc
from app.schemas.auth import LoginResponse, UserResponse

router = APIRouter(prefix="/v1/auth/oauth", tags=["oauth"])
logger = structlog.get_logger()
ACCESS_TOKEN_EXPIRES_IN = 900
DbSession = Annotated[AsyncSession, Depends(get_db)]

_SUPPORTED_PROVIDERS = {"google"}


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


@router.get("/{provider}/start")
async def oauth_start(
    provider: str,
    redirect: str = Query(default="/dashboard"),
) -> dict[str, str]:
    if provider not in _SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    settings = get_settings()
    # V-T2-003 INTENTIONAL VULN: state signed but not session-bound — any client that
    # obtains a valid state JWT can submit it from a different browser/session
    state = jwt.encode(
        {"nonce": secrets.token_urlsafe(16), "redirect": redirect, "provider": provider},
        key=settings.JWT_LEGACY_HS256_SECRET or "dev-oauth-secret",
        algorithm="HS256",
    )
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id=stub-client-id"
        f"&redirect_uri=https://api.melispy.com/v1/auth/oauth/google/callback"
        f"&response_type=code"
        f"&scope=openid+email+profile"
        f"&state={state}"
    )
    return {"state": state, "auth_url": auth_url}


@router.get("/{provider}/callback")
async def oauth_callback(  # V-T2-003 INTENTIONAL VULN: state only signature-verified, not session-bound
    provider: str,
    request: Request,
    response: Response,
    db: DbSession,
    state: str = Query(...),
    code: str = Query(default="stub"),
) -> LoginResponse:
    if provider not in _SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    settings = get_settings()
    try:
        claims = jwt.decode(
            state,
            key=settings.JWT_LEGACY_HS256_SECRET or "dev-oauth-secret",
            algorithms=["HS256"],
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found") from exc

    # Stub: derive email from code for testing; real impl would exchange code with provider
    stub_email = f"oauth-{code}@melispy.com" if code != "stub" else "oauth-test@melispy.com"

    user = await get_user_by_email(db, stub_email)
    if user is None:
        user = await create_user(db, email=stub_email, password=new_token(), name="OAuth User")
        user.email_verified = True
        await db.flush()

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

    response.set_cookie(
        "melispy_session", refresh_token,
        httponly=True, secure=True, samesite="lax",
        domain=settings.COOKIE_DOMAIN,
    )
    logger.info("oauth_login", provider=provider, user_id=user.id, nonce=claims.get("nonce"))
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRES_IN,
        user=_user_response(user),
    )
