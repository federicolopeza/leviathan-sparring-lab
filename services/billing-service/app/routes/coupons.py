from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.coupons import create_coupon, list_coupons
from app.deps.auth import Principal, get_current_principal, require_admin
from app.deps.db import get_db
from app.models import Coupon
from app.schemas.billing import CouponCreateRequest, CouponResponse

router = APIRouter(prefix="/v1/billing/coupons", tags=["billing-coupons"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


def coupon_response(coupon: Coupon) -> CouponResponse:
    return CouponResponse.model_validate(
        {
            "id": coupon.id,
            "code": coupon.code,
            "discount_pct": coupon.discount_pct,
            "discount_cents": coupon.discount_cents,
            "valid_from": coupon.valid_from,
            "valid_until": coupon.valid_until,
            "max_uses": coupon.max_uses,
            "used_count": coupon.used_count,
            "created_at": coupon.created_at,
        }
    )


@router.post("", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
async def post_coupon(
    payload: CouponCreateRequest,
    principal: CurrentPrincipal,
    db: DbSession,
) -> CouponResponse:
    await require_admin(principal)
    coupon = await create_coupon(
        db,
        code=payload.code,
        discount_pct=payload.discount_pct,
        discount_cents=payload.discount_cents,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        max_uses=payload.max_uses,
    )
    await db.commit()
    return coupon_response(coupon)


@router.get("", response_model=list[CouponResponse])
async def get_coupons(principal: CurrentPrincipal, db: DbSession) -> list[CouponResponse]:
    await require_admin(principal)
    coupons = await list_coupons(db)
    return [coupon_response(coupon) for coupon in coupons]
