from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from melispy_shared import issue_jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crud.tokens import (
    create_email_verify_token,
    create_password_reset_token,
    get_valid_email_verify_token,
    get_valid_password_reset_token,
    hash_token,
    new_token,
)
from app.crud.users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    verify_password,
)
from app.deps.auth import Principal, get_current_principal
from app.deps.db import get_db
from app.models import Session
from app.models.base import now_utc
from app.schemas.auth import (
    ForgotRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    ResetRequest,
    SignupRequest,
    SignupResponse,
    UserResponse,
    VerifyRequest,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])
logger = structlog.get_logger()
ACCESS_TOKEN_EXPIRES_IN = 900
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


def _client_ip(request: Request) -> str:
    if request.client is None:
        return "unknown"
    return request.client.host


def _user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")


def _access_token(user_id: str, session_id: str, email: str) -> str:
    settings = get_settings()
    return issue_jwt(
        {"sub": user_id, "sid": session_id, "email": email},
        settings.JWT_PRIVATE_KEY_PEM or "",
        alg="RS256",
        expires_in=ACCESS_TOKEN_EXPIRES_IN,
    )


def _user_response(user: object) -> UserResponse:
    return UserResponse.model_validate(
        {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "email_verified": user.email_verified,
            "is_admin": user.is_admin,
        }
    )


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, db: DbSession) -> SignupResponse:
    if await get_user_by_email(db, str(payload.email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already exists")
    try:
        user = await create_user(
            db,
            email=str(payload.email),
            password=payload.password,
            name=payload.name,
        )
        verify_row, _verify_token = await create_email_verify_token(db, user.id)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already exists",
        ) from exc
    logger.info("email_verify_token_issued", user_id=user.id, token_id=verify_row.id)
    return SignupResponse(user_id=user.id)


@router.post("/verify")
async def verify_email(payload: VerifyRequest, db: DbSession) -> dict[str, bool]:
    token = await get_valid_email_verify_token(db, payload.token)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")
    user = await get_user_by_id(db, token.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")
    token.used_at = now_utc()
    user.email_verified = True
    await db.commit()
    return {"ok": True}


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession,
) -> LoginResponse:
    user = await get_user_by_email(db, str(payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")

    refresh_token = new_token()
    session = Session(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        ip=_client_ip(request),
        user_agent=_user_agent(request),
    )
    db.add(session)
    await db.flush()
    access_token = _access_token(user.id, session.id, user.email)
    await db.commit()

    settings = get_settings()
    response.set_cookie(
        "melispy_session",
        refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        domain=settings.COOKIE_DOMAIN,  # V-T3-005 INTENTIONAL VULN: wide cookie domain
    )
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRES_IN,
        user=_user_response(user),
    )


@router.post("/forgot")
async def forgot_password(payload: ForgotRequest, db: DbSession) -> dict[str, bool]:
    user = await get_user_by_email(db, str(payload.email))
    if user is not None:
        reset_row, _reset_token = await create_password_reset_token(db, user.id)
        await db.commit()
        logger.info("password_reset_token_issued", user_id=user.id, token_id=reset_row.id)
    return {"ok": True}


@router.post("/reset")
async def reset_password(payload: ResetRequest, db: DbSession) -> dict[str, bool]:
    token = await get_valid_password_reset_token(db, payload.token)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")
    user = await get_user_by_id(db, token.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")
    user.password_hash = hash_password(payload.new_password)
    token.used_at = now_utc()
    await db.commit()
    return {"ok": True}


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(payload: RefreshRequest, db: DbSession) -> RefreshResponse:
    result = await db.execute(
        select(Session).where(
            Session.refresh_token_hash == hash_token(payload.refresh_token),
            Session.revoked_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")
    user = await get_user_by_id(db, session.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")
    new_refresh_token = new_token()
    session.refresh_token_hash = hash_token(new_refresh_token)
    session.last_seen_at = now_utc()
    access_token = _access_token(user.id, session.id, user.email)
    await db.commit()
    return RefreshResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRES_IN,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    principal: CurrentPrincipal,
    db: DbSession,
) -> Response:
    principal.session.revoked_at = now_utc()
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
