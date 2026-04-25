from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.carts import (
    add_coupon_to_cart,
    calculate_totals,
    get_current_cart,
    remove_coupon_from_cart,
    replace_cart,
)
from app.crud.checkouts import create_completed_checkout
from app.crud.coupons import get_coupon_by_code
from app.crud.invoices import create_paid_invoice
from app.crud.plans import get_plan
from app.deps.auth import Principal, get_current_principal
from app.deps.db import get_db
from app.models import Cart, Checkout
from app.routes.plans import plan_response
from app.schemas.billing import (
    CartCouponRequest,
    CartCreateRequest,
    CartResponse,
    CheckoutDetailResponse,
    CheckoutRequest,
    CheckoutResponse,
    CouponSummary,
)

router = APIRouter(prefix="/v1/billing", tags=["billing"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


def _empty_cart(principal: Principal) -> CartResponse:
    return CartResponse(
        id=None,
        user_id=principal.user_id,
        org_id=principal.org_id,
        plan=None,
        quantity=0,
        subtotal_cents=0,
        discount_cents=0,
        total_cents=0,
        coupons=[],
    )


def cart_response(cart: Cart) -> CartResponse:
    subtotal, discount, total = calculate_totals(cart)
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        org_id=cart.org_id,
        plan=plan_response(cart.plan),
        quantity=cart.quantity,
        subtotal_cents=subtotal,
        discount_cents=discount,
        total_cents=total,
        coupons=[
            CouponSummary(
                id=item.coupon.id,
                code=item.coupon.code,
                discount_cents=_coupon_discount(
                    subtotal,
                    item.coupon.discount_pct,
                    item.coupon.discount_cents,
                ),
                applied_at=item.applied_at,
            )
            for item in cart.coupons
        ],
    )


def _coupon_discount(
    subtotal_cents: int,
    discount_pct: int | None,
    discount_cents: int | None,
) -> int:
    if discount_pct is not None:
        return subtotal_cents * discount_pct // 100
    return int(discount_cents or 0)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@router.get("/cart", response_model=CartResponse)
async def get_cart(principal: CurrentPrincipal, db: DbSession) -> CartResponse:
    cart = await get_current_cart(db, user_id=principal.user_id, org_id=principal.org_id)
    if cart is None:
        return _empty_cart(principal)
    return cart_response(cart)


@router.post("/cart", response_model=CartResponse)
async def post_cart(
    payload: CartCreateRequest,
    principal: CurrentPrincipal,
    db: DbSession,
) -> CartResponse:
    plan = await get_plan(db, payload.plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    cart = await replace_cart(
        db,
        user_id=principal.user_id,
        org_id=principal.org_id,
        plan=plan,
        quantity=payload.quantity,
    )
    await db.commit()
    cart = await get_current_cart(db, user_id=cart.user_id, org_id=cart.org_id)
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return cart_response(cart)


@router.post("/cart/coupon", response_model=CartResponse)
async def post_cart_coupon(
    payload: CartCouponRequest,
    principal: CurrentPrincipal,
    db: DbSession,
) -> CartResponse:
    cart = await get_current_cart(db, user_id=principal.user_id, org_id=principal.org_id)
    coupon = await get_coupon_by_code(db, payload.coupon_code)
    now = datetime.now(UTC)
    if cart is None or coupon is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    if not (_as_utc(coupon.valid_from) <= now <= _as_utc(coupon.valid_until)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="coupon exhausted")
    await add_coupon_to_cart(db, cart=cart, coupon=coupon)
    await db.commit()
    cart = await get_current_cart(db, user_id=principal.user_id, org_id=principal.org_id)
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return cart_response(cart)


@router.delete("/cart/coupon/{coupon_id}", response_model=CartResponse)
async def delete_cart_coupon(
    coupon_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> CartResponse:
    cart = await get_current_cart(db, user_id=principal.user_id, org_id=principal.org_id)
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    removed = await remove_coupon_from_cart(db, cart=cart, coupon_id=coupon_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    await db.commit()
    cart = await get_current_cart(db, user_id=principal.user_id, org_id=principal.org_id)
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return cart_response(cart)


@router.post("/checkout", response_model=CheckoutResponse)
async def post_checkout(
    payload: CheckoutRequest,
    principal: CurrentPrincipal,
    db: DbSession,
) -> CheckoutResponse:
    cart = await get_current_cart(db, user_id=principal.user_id, org_id=principal.org_id)
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    # V-T4-001 INTENTIONAL VULN: idempotency_key is not enforced before checkout insert.
    await asyncio.sleep(0)
    subtotal, discount, total = calculate_totals(cart)
    checkout = await create_completed_checkout(
        db,
        cart_id=cart.id,
        user_id=cart.user_id,
        org_id=cart.org_id,
        plan_id=cart.plan_id,
        quantity=cart.quantity,
        subtotal_cents=subtotal,
        discount_cents=discount,
        total_cents=total,
        idempotency_key=payload.idempotency_key,
    )
    invoice = await create_paid_invoice(
        db,
        checkout_id=checkout.id,
        user_id=checkout.user_id,
        org_id=checkout.org_id,
        total_cents=checkout.total_cents,
        currency=cart.plan.currency,
    )
    await db.commit()
    return CheckoutResponse(
        checkout_id=checkout.id,
        invoice_id=invoice.id,
        total_cents=checkout.total_cents,
        status=checkout.status,
    )


@router.get("/checkouts/{checkout_id}", response_model=CheckoutDetailResponse)
async def get_checkout(
    checkout_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> CheckoutDetailResponse:
    result = await db.execute(select(Checkout).where(Checkout.id == checkout_id))
    checkout = result.scalar_one_or_none()
    if checkout is None or checkout.user_id != principal.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return CheckoutDetailResponse.model_validate(
        {
            "id": checkout.id,
            "cart_id": checkout.cart_id,
            "user_id": checkout.user_id,
            "org_id": checkout.org_id,
            "plan_id": checkout.plan_id,
            "quantity": checkout.quantity,
            "subtotal_cents": checkout.subtotal_cents,
            "discount_cents": checkout.discount_cents,
            "total_cents": checkout.total_cents,
            "status": checkout.status,
            "idempotency_key": checkout.idempotency_key,
            "created_at": checkout.created_at,
            "completed_at": checkout.completed_at,
        }
    )
