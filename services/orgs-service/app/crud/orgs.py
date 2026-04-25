from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Org, OrgMembership, OrgPlan, OrgRole


async def create_org(
    db: AsyncSession,
    *,
    name: str,
    plan: OrgPlan,
    region: str,
    owner_user_id: str,
) -> Org:
    org = Org(name=name.strip(), plan=plan, region=region.strip(), owner_user_id=owner_user_id)
    db.add(org)
    await db.flush()
    membership = OrgMembership(org_id=org.id, user_id=owner_user_id, role=OrgRole.OWNER)
    db.add(membership)
    await db.flush()
    return org


async def get_org(db: AsyncSession, org_id: str) -> Org | None:
    result = await db.execute(select(Org).where(Org.id == org_id))
    return result.scalar_one_or_none()


async def list_orgs_for_user(db: AsyncSession, user_id: str) -> list[Org]:
    result = await db.execute(
        select(Org)
        .join(OrgMembership, OrgMembership.org_id == Org.id)
        .where(OrgMembership.user_id == user_id)
        .order_by(Org.created_at)
    )
    return list(result.scalars().all())


async def count_members(db: AsyncSession, org_id: str) -> int:
    result = await db.execute(
        select(func.count()).select_from(OrgMembership).where(OrgMembership.org_id == org_id)
    )
    return int(result.scalar_one())
