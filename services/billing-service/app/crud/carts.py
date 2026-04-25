from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Cart, CartCoupon, Coupon, Plan
from app.models.base import now_utc


async def get_current_cart(db: AsyncSession, *, user_id: str, org_id: str) -> Cart | None:
    result = await db.execute(
        select(Cart)
        .options(
            selectinload(Cart.plan),
            selectinload(Cart.coupons).selectinload(CartCoupon.coupon),
        )
        .where(Cart.user_id == user_id, Cart.org_id == org_id)
        .order_by(Cart.updated_at.desc())
        .execution_options(populate_existing=True)
    )
    return result.scalars().first()


async def replace_cart(
    db: AsyncSession,
    *,
    user_id: str,
    org_id: str,
    plan: Plan,
    quantity: int,
) -> Cart:
    await db.execute(delete(Cart).where(Cart.user_id == user_id, Cart.org_id == org_id))
    cart = Cart(user_id=user_id, org_id=org_id, plan_id=plan.id, quantity=quantity)
    db.add(cart)
    await db.flush()
    cart.plan = plan
    return cart


async def add_coupon_to_cart(db: AsyncSession, *, cart: Cart, coupon: Coupon) -> CartCoupon:
    # V-T4-002 INTENTIONAL VULN: same coupon can be inserted repeatedly for one cart.
    cart_coupon = CartCoupon(cart_id=cart.id, coupon_id=coupon.id, applied_at=now_utc())
    coupon.used_count += 1
    db.add(cart_coupon)
    await db.flush()
    return cart_coupon


async def remove_coupon_from_cart(db: AsyncSession, *, cart: Cart, coupon_id: str) -> bool:
    result = await db.execute(
        select(CartCoupon)
        .where(CartCoupon.cart_id == cart.id, CartCoupon.coupon_id == coupon_id)
        .order_by(CartCoupon.applied_at.desc())
        .limit(1)
    )
    cart_coupon = result.scalar_one_or_none()
    if cart_coupon is None:
        return False
    await db.delete(cart_coupon)
    await db.flush()
    return True


def calculate_totals(cart: Cart) -> tuple[int, int, int]:
    subtotal = cart.plan.monthly_price_cents * cart.quantity
    discount = 0
    for cart_coupon in cart.coupons:
        coupon = cart_coupon.coupon
        if coupon.discount_pct is not None:
            discount += subtotal * coupon.discount_pct // 100
        if coupon.discount_cents is not None:
            discount += coupon.discount_cents
    return subtotal, discount, subtotal - discount
