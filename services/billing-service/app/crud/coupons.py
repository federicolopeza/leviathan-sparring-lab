from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Coupon


async def create_coupon(
    db: AsyncSession,
    *,
    code: str,
    discount_pct: int | None,
    discount_cents: int | None,
    valid_from: datetime,
    valid_until: datetime,
    max_uses: int | None,
) -> Coupon:
    coupon = Coupon(
        code=code.strip().upper(),
        discount_pct=discount_pct,
        discount_cents=discount_cents,
        valid_from=valid_from,
        valid_until=valid_until,
        max_uses=max_uses,
    )
    db.add(coupon)
    await db.flush()
    return coupon


async def list_coupons(db: AsyncSession) -> list[Coupon]:
    result = await db.execute(select(Coupon).order_by(Coupon.created_at))
    return list(result.scalars().all())


async def get_coupon_by_code(db: AsyncSession, code: str) -> Coupon | None:
    result = await db.execute(select(Coupon).where(Coupon.code == code.strip().upper()))
    return result.scalar_one_or_none()
