"""Database engine and tenant helpers."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://melispy:melispy@postgres:5432/melispy",
)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


@asynccontextmanager
async def with_tenant(session: AsyncSession, tenant_id: UUID | str) -> AsyncIterator[AsyncSession]:
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )
    try:
        yield session
    finally:
        await session.execute(text("SELECT set_config('app.current_tenant_id', '', true)"))
