from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.crud.invitations import (
    create_invitation,
    get_invitation_by_token,
    hash_token,
    is_expired,
    list_pending_invitations,
)
from app.crud.members import add_member, get_membership
from app.deps.auth import Principal, get_current_principal
from app.deps.db import get_db
from app.deps.membership import require_owner_or_admin
from app.models import OrgInvitation, OrgMembership
from app.models.base import now_utc
from app.schemas.invitations import (
    InvitationAcceptRequest,
    InvitationCreate,
    InvitationCreateResponse,
    InvitationPendingResponse,
)
from app.schemas.members import MemberResponse

router = APIRouter(prefix="/v1/orgs", tags=["invitations"])
logger = structlog.get_logger()
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


def _pending_response(invitation: OrgInvitation) -> InvitationPendingResponse:
    return InvitationPendingResponse.model_validate(
        {
            "id": invitation.id,
            "email": invitation.email,
            "role": invitation.role,
            "expires_at": invitation.expires_at,
        }
    )


def _member_response(membership: OrgMembership) -> MemberResponse:
    return MemberResponse.model_validate(
        {
            "id": membership.id,
            "org_id": membership.org_id,
            "user_id": membership.user_id,
            "role": membership.role,
            "created_at": membership.created_at,
        }
    )


@router.post("/invitations/accept", response_model=MemberResponse)
async def accept_invitation(
    payload: InvitationAcceptRequest,
    principal: CurrentPrincipal,
    db: DbSession,
) -> MemberResponse:
    invitation = await get_invitation_by_token(db, payload.token)
    if invitation is None or is_expired(invitation.expires_at):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid invitation")
    if await get_membership(db, org_id=invitation.org_id, user_id=principal.user_id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="already member")
    # Atomic claim of used_at — prevents TOCTOU race where concurrent requests both pass
    # the `used_at IS NULL` check before either commits.
    claim = await db.execute(
        update(OrgInvitation)
        .where(OrgInvitation.id == invitation.id, OrgInvitation.used_at.is_(None))
        .values(used_at=now_utc())
    )
    if claim.rowcount != 1:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid invitation")
    try:
        membership = await add_member(
            db,
            org_id=invitation.org_id,
            user_id=principal.user_id,
            role=invitation.role,
        )
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="already member") from exc
    return _member_response(membership)


@router.post("/{org_id}/invitations", response_model=InvitationCreateResponse)
async def post_invitation(
    org_id: str,
    payload: InvitationCreate,
    principal: CurrentPrincipal,
    db: DbSession,
) -> InvitationCreateResponse:
    await require_owner_or_admin(db, org_id=org_id, user_id=principal.user_id)
    settings = get_settings()
    # TODO Phase 2: V-T3-006 INTENTIONAL — replace with 4-byte hex predictable token
    token = secrets.token_urlsafe(32)
    expires_at = now_utc() + timedelta(days=settings.INVITATION_TTL_DAYS)
    invitation = await create_invitation(
        db,
        org_id=org_id,
        email=payload.email,
        role=payload.role,
        token_hash=hash_token(token),
        expires_at=expires_at,
    )
    await db.commit()
    logger.info("org_invitation_issued", org_id=org_id, token_id=invitation.id)
    return InvitationCreateResponse(invitation_id=invitation.id, expires_at=invitation.expires_at)


@router.get("/{org_id}/invitations", response_model=list[InvitationPendingResponse])
async def get_invitations(
    org_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> list[InvitationPendingResponse]:
    await require_owner_or_admin(db, org_id=org_id, user_id=principal.user_id)
    invitations = await list_pending_invitations(db, org_id)
    return [_pending_response(invitation) for invitation in invitations]
