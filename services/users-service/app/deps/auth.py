from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from melispy_shared import verify_jwt
from sqlalchemy import Boolean, DateTime, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import get_settings
from app.deps.db import get_auth_db

AuthSession = Annotated[AsyncSession, Depends(get_auth_db)]
AuthorizationHeader = Annotated[str | None, Header()]


class AuthBase(DeclarativeBase):
    pass


class AuthUser(AuthBase):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@dataclass(frozen=True)
class Principal:
    user: AuthUser


async def get_auth_user(db: AsyncSession, user_id: str) -> AuthUser | None:
    result = await db.execute(select(AuthUser).where(AuthUser.id == user_id))
    return result.scalar_one_or_none()


async def get_current_principal(
    auth_db: AuthSession,
    authorization: AuthorizationHeader = None,
) -> Principal:
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
    user = await get_auth_user(auth_db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")
    return Principal(user=user)
