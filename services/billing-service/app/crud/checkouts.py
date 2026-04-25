from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Checkout, CheckoutStatus
from app.models.base import now_utc


async def create_completed_checkout(
    db: AsyncSession,
    *,
    cart_id: str,
    user_id: str,
    org_id: str,
    plan_id: str,
    quantity: int,
    subtotal_cents: int,
    discount_cents: int,
    total_cents: int,
    idempotency_key: str | None,
) -> Checkout:
    checkout = Checkout(
        cart_id=cart_id,
        user_id=user_id,
        org_id=org_id,
        plan_id=plan_id,
        quantity=quantity,
        subtotal_cents=subtotal_cents,
        discount_cents=discount_cents,
        total_cents=total_cents,
        status=CheckoutStatus.COMPLETED,
        idempotency_key=idempotency_key,
        completed_at=now_utc(),
    )
    db.add(checkout)
    await db.flush()
    return checkout
