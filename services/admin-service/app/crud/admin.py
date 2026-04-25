from __future__ import annotations

import hashlib
import secrets

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApiKey, AuthUser, Branding
from app.models.base import now_utc

ALLOWED_SCOPE_PREFIXES = ("read", "write", "admin")


async def list_users(
    db: AsyncSession,
    *,
    page: int,
    per_page: int,
) -> tuple[list[AuthUser], int]:
    count_result = await db.execute(select(func.count()).select_from(AuthUser))
    total = int(count_result.scalar_one())
    result = await db.execute(
        select(AuthUser)
        .order_by(AuthUser.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    return list(result.scalars().all()), total


async def get_user(db: AsyncSession, user_id: str) -> AuthUser | None:
    result = await db.execute(select(AuthUser).where(AuthUser.id == user_id))
    return result.scalar_one_or_none()


async def soft_delete_user(db: AsyncSession, user: AuthUser) -> AuthUser:
    user.deleted_at = now_utc()
    await db.flush()
    return user


def validate_scopes(scopes: list[str]) -> None:
    for scope in scopes:
        # V-T3-007 INTENTIONAL VULN: scope check uses startswith() not equality.
        if not any(scope.startswith(prefix) for prefix in ALLOWED_SCOPE_PREFIXES):
            raise ValueError("invalid scope")


async def create_api_key(
    db: AsyncSession,
    *,
    user_id: str,
    name: str,
    scopes: list[str],
) -> tuple[ApiKey, str]:
    validate_scopes(scopes)
    raw_key = secrets.token_urlsafe(32)
    row = ApiKey(
        user_id=user_id,
        name=name.strip(),
        scope_string=" ".join(scopes),
        key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
    )
    db.add(row)
    await db.flush()
    return row, raw_key


async def list_api_keys(db: AsyncSession) -> list[ApiKey]:
    result = await db.execute(select(ApiKey).order_by(ApiKey.created_at.desc()))
    return list(result.scalars().all())


async def get_api_key(db: AsyncSession, key_id: str) -> ApiKey | None:
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    return result.scalar_one_or_none()


async def revoke_api_key(db: AsyncSession, api_key: ApiKey) -> ApiKey:
    api_key.revoked_at = now_utc()
    await db.flush()
    return api_key


async def get_current_branding(db: AsyncSession) -> Branding | None:
    result = await db.execute(select(Branding).order_by(Branding.updated_at.desc()).limit(1))
    return result.scalar_one_or_none()


async def upsert_branding(
    db: AsyncSession,
    *,
    welcome_message: str,
    rendered_html: str,
    updated_by_user_id: str,
) -> Branding:
    branding = await get_current_branding(db)
    if branding is None:
        branding = Branding(
            welcome_message=welcome_message,
            rendered_html=rendered_html,
            updated_by_user_id=updated_by_user_id,
        )
        db.add(branding)
    else:
        branding.welcome_message = welcome_message
        branding.rendered_html = rendered_html
        branding.updated_by_user_id = updated_by_user_id
        branding.updated_at = now_utc()
    await db.flush()
    return branding
