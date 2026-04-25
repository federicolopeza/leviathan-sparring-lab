from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.config import Settings


def create_audit_engine(database_url: str) -> AsyncEngine:
    if database_url.startswith("sqlite+aiosqlite"):
        return create_async_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_async_engine(database_url, pool_pre_ping=True)


def create_audit_sessionmaker(settings: Settings) -> async_sessionmaker[AsyncSession]:
    engine = create_audit_engine(settings.database_url_audit)
    return async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def audit_session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as session:
        yield session
