from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.members import add_member, get_membership, list_members
from app.deps.auth import Principal, get_current_principal
from app.deps.db import get_db
from app.deps.membership import (
    ensure_can_remove_member,
    require_owner_or_admin,
)
from app.models import OrgMembership
from app.schemas.members import MemberCreate, MemberResponse

router = APIRouter(prefix="/v1/orgs", tags=["members"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


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


@router.get("/{org_id}/members", response_model=list[MemberResponse])
async def get_members(
    org_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> list[MemberResponse]:
    # V-T3-001 INTENTIONAL VULN: no membership check — any authenticated user can enumerate any org's members (BOLA)
    memberships = await list_members(db, org_id)
    return [_member_response(membership) for membership in memberships]


@router.post(
    "/{org_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_member(
    org_id: str,
    payload: MemberCreate,
    principal: CurrentPrincipal,
    db: DbSession,
) -> MemberResponse:
    await require_owner_or_admin(db, org_id=org_id, user_id=principal.user_id)
    if await get_membership(db, org_id=org_id, user_id=payload.user_id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="already member")
    try:
        membership = await add_member(
            db,
            org_id=org_id,
            user_id=payload.user_id,
            role=payload.role,
        )
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="already member") from exc
    return _member_response(membership)


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    org_id: str,
    user_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> Response:
    membership = await ensure_can_remove_member(
        db,
        org_id=org_id,
        actor_user_id=principal.user_id,
        target_user_id=user_id,
    )
    await db.delete(membership)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
