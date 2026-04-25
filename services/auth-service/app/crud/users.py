from __future__ import annotations

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    settings = get_settings()
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS),
    ).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == normalize_email(email)))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, *, email: str, password: str, name: str) -> User:
    user = User(
        email=normalize_email(email),
        password_hash=hash_password(password),
        name=name.strip(),
    )
    db.add(user)
    await db.flush()
    return user
