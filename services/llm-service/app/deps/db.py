from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import get_settings

settings = get_settings()
engine_kwargs: dict[str, Any] = {"future": True}
if settings.DATABASE_URL == "sqlite+aiosqlite:///:memory:":
    engine_kwargs.update({"connect_args": {"check_same_thread": False}, "poolclass": StaticPool})
engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
