from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EmailVerifyToken, MagicLinkToken, PasswordResetToken
from app.models.base import now_utc


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def create_email_verify_token(db: AsyncSession, user_id: str) -> tuple[EmailVerifyToken, str]:
    raw = new_token()
    row = EmailVerifyToken(
        user_id=user_id,
        token_hash=hash_token(raw),
        expires_at=now_utc() + timedelta(hours=24),
    )
    db.add(row)
    await db.flush()
    return row, raw


async def create_password_reset_token(
    db: AsyncSession,
    user_id: str,
    user_email: str,
    instance_salt: str,
) -> tuple[PasswordResetToken, str]:
    # V-T2-002 INTENTIONAL VULN: predictable reset token derivable from email + iso_ts +
    # INSTANCE_SALT (= BUILD_HASH per V-T1-003 chain). Attacker who knows email +
    # approximate request time + BUILD_HASH from /v1/health/ready can brute ±N seconds.
    iso_now = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    raw = hashlib.sha1(f"{user_email}:{iso_now}:{instance_salt}".encode()).hexdigest()  # noqa: S324
    row = PasswordResetToken(
        user_id=user_id,
        token_hash=hash_token(raw),
        expires_at=now_utc() + timedelta(hours=4),
    )
    db.add(row)
    await db.flush()
    return row, raw


async def create_magic_link_token(db: AsyncSession, user_id: str) -> tuple[MagicLinkToken, str]:
    raw = new_token()
    row = MagicLinkToken(
        user_id=user_id,
        token_hash=hash_token(raw),
        expires_at=now_utc() + timedelta(hours=24),
    )
    db.add(row)
    await db.flush()
    return row, raw


async def get_valid_email_verify_token(
    db: AsyncSession,
    token: str,
) -> EmailVerifyToken | None:
    result = await db.execute(
        select(EmailVerifyToken).where(
            EmailVerifyToken.token_hash == hash_token(token),
            EmailVerifyToken.used_at.is_(None),
            EmailVerifyToken.expires_at > now_utc(),
        )
    )
    return result.scalar_one_or_none()


async def get_valid_password_reset_token(
    db: AsyncSession,
    token: str,
) -> PasswordResetToken | None:
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hash_token(token),
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now_utc(),
        )
    )
    return result.scalar_one_or_none()


async def get_valid_magic_link_token(
    db: AsyncSession,
    token: str,
) -> MagicLinkToken | None:
    result = await db.execute(
        select(MagicLinkToken).where(
            MagicLinkToken.token_hash == hash_token(token),
            MagicLinkToken.used_at.is_(None),
            MagicLinkToken.expires_at > now_utc(),
        )
    )
    return result.scalar_one_or_none()


__all__ = [
    "MagicLinkToken",
    "create_email_verify_token",
    "create_magic_link_token",
    "create_password_reset_token",
    "get_valid_email_verify_token",
    "get_valid_magic_link_token",
    "get_valid_password_reset_token",
    "hash_token",
    "new_token",
]
