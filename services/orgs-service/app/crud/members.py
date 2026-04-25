from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OrgMembership, OrgRole


async def get_membership(
    db: AsyncSession,
    *,
    org_id: str,
    user_id: str,
) -> OrgMembership | None:
    result = await db.execute(
        select(OrgMembership).where(
            OrgMembership.org_id == org_id,
            OrgMembership.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def list_members(db: AsyncSession, org_id: str) -> list[OrgMembership]:
    result = await db.execute(
        select(OrgMembership)
        .where(OrgMembership.org_id == org_id)
        .order_by(OrgMembership.created_at)
    )
    return list(result.scalars().all())


async def add_member(
    db: AsyncSession,
    *,
    org_id: str,
    user_id: str,
    role: OrgRole,
) -> OrgMembership:
    membership = OrgMembership(org_id=org_id, user_id=user_id, role=role)
    db.add(membership)
    await db.flush()
    return membership


async def count_owners(db: AsyncSession, org_id: str) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(OrgMembership)
        .where(OrgMembership.org_id == org_id, OrgMembership.role == OrgRole.OWNER)
    )
    return int(result.scalar_one())
