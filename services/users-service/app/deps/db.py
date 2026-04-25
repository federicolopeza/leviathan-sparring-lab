from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL, future=True)
auth_engine = create_async_engine(settings.DATABASE_URL_AUTH, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
AuthSessionLocal = async_sessionmaker(auth_engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def get_auth_db() -> AsyncIterator[AsyncSession]:
    async with AuthSessionLocal() as session:
        yield session
