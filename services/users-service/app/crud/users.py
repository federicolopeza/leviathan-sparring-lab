from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserProfile


async def get_profile(db: AsyncSession, user_id: str) -> UserProfile | None:
    result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
    return result.scalar_one_or_none()


async def get_or_create_profile(db: AsyncSession, user_id: str) -> UserProfile:
    profile = await get_profile(db, user_id)
    if profile is not None:
        return profile
    profile = UserProfile(id=user_id)
    db.add(profile)
    await db.flush()
    return profile
