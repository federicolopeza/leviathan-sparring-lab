from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from melispy_shared import verify_jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crud.users import get_user_by_id
from app.deps.db import get_db
from app.models import Session, User
from app.models.base import now_utc

DbSession = Annotated[AsyncSession, Depends(get_db)]
AuthorizationHeader = Annotated[str | None, Header()]


@dataclass(frozen=True)
class Principal:
    user: User
    session: Session


async def get_current_principal(
    db: DbSession,
    authorization: AuthorizationHeader = None,
) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")
    token = authorization.split(" ", 1)[1].strip()
    settings = get_settings()
    try:
        claims = verify_jwt(token, settings.JWT_PUBLIC_KEY_PEM or "", expected_alg="RS256")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found") from exc

    user_id = str(claims.get("sub", ""))
    session_id = str(claims.get("sid", ""))
    if not user_id or not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")

    user = await get_user_by_id(db, user_id)
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == user_id,
            Session.revoked_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()
    if user is None or session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Found")
    session.last_seen_at = now_utc()
    await db.flush()
    return Principal(user=user, session=session)
