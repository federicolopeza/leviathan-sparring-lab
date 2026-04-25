from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentRun, AgentRunStatus


async def create_agent_run(
    db: AsyncSession,
    *,
    user_id: str,
    org_id: str | None,
    name: str,
    input_json: dict[str, object],
) -> AgentRun:
    run = AgentRun(
        user_id=user_id,
        org_id=org_id,
        name=name,
        status=AgentRunStatus.QUEUED,
        input_json=input_json,
    )
    db.add(run)
    await db.flush()
    return run


async def list_agent_runs(db: AsyncSession, *, user_id: str) -> list[AgentRun]:
    result = await db.execute(
        select(AgentRun).where(AgentRun.user_id == user_id).order_by(AgentRun.created_at.desc())
    )
    return list(result.scalars().all())


async def get_agent_run(db: AsyncSession, *, run_id: str) -> AgentRun | None:
    result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
    return result.scalar_one_or_none()


async def cancel_agent_run(db: AsyncSession, *, run: AgentRun) -> AgentRun:
    run.status = AgentRunStatus.CANCELLED
    await db.flush()
    return run
