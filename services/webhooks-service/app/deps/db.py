from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import get_settings

settings = get_settings()


def _engine_kwargs(url: str) -> dict[str, object]:
    kwargs: dict[str, object] = {"future": True}
    if url.startswith("sqlite+aiosqlite") and ":memory:" in url:
        kwargs.update({"connect_args": {"check_same_thread": False}, "poolclass": StaticPool})
    return kwargs


engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs(settings.DATABASE_URL))
auth_engine = create_async_engine(
    settings.DATABASE_URL_AUTH,
    **_engine_kwargs(settings.DATABASE_URL_AUTH),
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
AuthSessionLocal = async_sessionmaker(auth_engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def get_auth_db() -> AsyncIterator[AsyncSession]:
    async with AuthSessionLocal() as session:
        yield session
