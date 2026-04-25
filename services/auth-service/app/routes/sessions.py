from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import Principal, get_current_principal
from app.deps.db import get_db
from app.models import Session
from app.models.base import now_utc
from app.schemas.auth import SessionResponse

router = APIRouter(prefix="/v1/auth", tags=["sessions"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    principal: CurrentPrincipal,
    db: DbSession,
) -> list[SessionResponse]:
    result = await db.execute(
        select(Session).where(
            Session.user_id == principal.user.id,
            Session.revoked_at.is_(None),
        )
    )
    return [
        SessionResponse(
            session_id=row.id,
            ip=row.ip,
            user_agent=row.user_agent,
            created_at=row.created_at,
            last_seen_at=row.last_seen_at,
        )
        for row in result.scalars().all()
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> Response:
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == principal.user.id,
            Session.revoked_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    session.revoked_at = now_utc()
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
