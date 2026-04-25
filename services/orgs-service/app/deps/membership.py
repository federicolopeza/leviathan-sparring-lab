from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.members import count_owners, get_membership
from app.crud.orgs import get_org
from app.models import Org, OrgMembership, OrgRole


async def require_org_membership(
    db: AsyncSession,
    *,
    org_id: str,
    user_id: str,
) -> tuple[Org, OrgMembership]:
    org = await get_org(db, org_id)
    membership = await get_membership(db, org_id=org_id, user_id=user_id)
    if org is None or membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return org, membership


async def require_owner(
    db: AsyncSession,
    *,
    org_id: str,
    user_id: str,
) -> tuple[Org, OrgMembership]:
    org, membership = await require_org_membership(db, org_id=org_id, user_id=user_id)
    if membership.role != OrgRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner role required")
    return org, membership


async def require_owner_or_admin(
    db: AsyncSession,
    *,
    org_id: str,
    user_id: str,
) -> tuple[Org, OrgMembership]:
    org, membership = await require_org_membership(db, org_id=org_id, user_id=user_id)
    if membership.role not in {OrgRole.OWNER, OrgRole.ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin role required")
    return org, membership


async def ensure_can_remove_member(
    db: AsyncSession,
    *,
    org_id: str,
    actor_user_id: str,
    target_user_id: str,
) -> OrgMembership:
    _org, actor_membership = await require_org_membership(
        db,
        org_id=org_id,
        user_id=actor_user_id,
    )
    target_membership = await get_membership(db, org_id=org_id, user_id=target_user_id)
    if target_membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    self_removal = actor_user_id == target_user_id and target_membership.role != OrgRole.OWNER
    if actor_membership.role != OrgRole.OWNER and not self_removal:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner role required")
    if target_membership.role == OrgRole.OWNER and await count_owners(db, org_id) <= 1:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="cannot remove only owner")
    return target_membership
