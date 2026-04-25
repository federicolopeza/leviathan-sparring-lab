from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from melispy_shared.models import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, dict[str, float]] = {}

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        bucket = self.data.setdefault(key, {})
        to_delete = [
            member
            for member, score in bucket.items()
            if float(min_score) <= score <= float(max_score)
        ]
        for member in to_delete:
            del bucket[member]
        return len(to_delete)

    async def zcard(self, key: str) -> int:
        return len(self.data.setdefault(key, {}))

    async def zadd(self, key: str, mapping: dict[str, float]) -> int:
        bucket = self.data.setdefault(key, {})
        bucket.update(mapping)
        return len(mapping)

    async def expire(self, key: str, seconds: int) -> bool:
        _ = key, seconds
        return True


@pytest_asyncio.fixture
async def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest_asyncio.fixture
async def async_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()
