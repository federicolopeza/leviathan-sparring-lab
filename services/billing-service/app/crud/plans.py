from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Plan, PlanCode

SEED_PLANS = [
    {
        "code": PlanCode.FREE,
        "name": "Free",
        "monthly_price_cents": 0,
        "currency": "USD",
        "description": "Baseline monitoring for small labs.",
        "features": {"seats": 1, "retention_days": 7},
    },
    {
        "code": PlanCode.PRO,
        "name": "Pro",
        "monthly_price_cents": 900,
        "currency": "USD",
        "description": "Team billing for recurring assessments.",
        "features": {"seats": 5, "retention_days": 30},
    },
    {
        "code": PlanCode.ENTERPRISE,
        "name": "Enterprise",
        "monthly_price_cents": 9900,
        "currency": "USD",
        "description": "Enterprise billing with dedicated workflows.",
        "features": {"seats": 50, "retention_days": 365},
    },
]


async def seed_plans(db: AsyncSession) -> None:
    for item in SEED_PLANS:
        result = await db.execute(select(Plan).where(Plan.code == item["code"]))
        if result.scalar_one_or_none() is None:
            db.add(Plan(**item))
    await db.flush()


async def list_plans(db: AsyncSession) -> list[Plan]:
    await seed_plans(db)
    result = await db.execute(select(Plan).order_by(Plan.monthly_price_cents))
    return list(result.scalars().all())


async def get_plan(db: AsyncSession, plan_id: str) -> Plan | None:
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    return result.scalar_one_or_none()
