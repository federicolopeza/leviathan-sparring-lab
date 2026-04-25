from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OrgInvitation, OrgRole


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def is_expired(expires_at: datetime) -> bool:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= datetime.now(UTC)


async def create_invitation(
    db: AsyncSession,
    *,
    org_id: str,
    email: str,
    role: OrgRole,
    token_hash: str,
    expires_at: datetime,
) -> OrgInvitation:
    invitation = OrgInvitation(
        org_id=org_id,
        email=email.strip().lower(),
        role=role,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(invitation)
    await db.flush()
    return invitation


async def get_invitation_by_token(db: AsyncSession, token: str) -> OrgInvitation | None:
    result = await db.execute(
        select(OrgInvitation).where(OrgInvitation.token_hash == hash_token(token))
    )
    return result.scalar_one_or_none()


async def list_pending_invitations(db: AsyncSession, org_id: str) -> list[OrgInvitation]:
    result = await db.execute(
        select(OrgInvitation)
        .where(OrgInvitation.org_id == org_id, OrgInvitation.used_at.is_(None))
        .order_by(OrgInvitation.created_at)
    )
    return list(result.scalars().all())
