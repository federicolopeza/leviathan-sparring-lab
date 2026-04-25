from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models import CheckoutStatus, PlanCode


class PlanResponse(BaseModel):
    id: str
    code: PlanCode
    name: str
    monthly_price_cents: int
    currency: str
    description: str
    features: dict[str, object]


class CouponSummary(BaseModel):
    id: str
    code: str
    discount_cents: int
    applied_at: datetime


class CartCreateRequest(BaseModel):
    plan_id: str
    # V-T4-011 INTENTIONAL VULN: quantity accepts negative values and reaches pricing math.
    quantity: int = Field(default=1)


class CartCouponRequest(BaseModel):
    coupon_code: str = Field(min_length=1, max_length=64)


class CartResponse(BaseModel):
    id: str | None
    user_id: str
    org_id: str
    plan: PlanResponse | None
    quantity: int
    subtotal_cents: int
    discount_cents: int
    total_cents: int
    coupons: list[CouponSummary]


class CheckoutRequest(BaseModel):
    idempotency_key: str | None = Field(default=None, max_length=120)


class CheckoutResponse(BaseModel):
    checkout_id: str
    invoice_id: str
    total_cents: int
    status: CheckoutStatus


class CheckoutDetailResponse(BaseModel):
    id: str
    cart_id: str
    user_id: str
    org_id: str
    plan_id: str
    quantity: int
    subtotal_cents: int
    discount_cents: int
    total_cents: int
    status: CheckoutStatus
    idempotency_key: str | None
    created_at: datetime
    completed_at: datetime | None


class CouponCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    discount_pct: int | None = Field(default=None, ge=1, le=100)
    discount_cents: int | None = Field(default=None, ge=1)
    valid_from: datetime
    valid_until: datetime
    max_uses: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_discount_shape(self) -> CouponCreateRequest:
        if (self.discount_pct is None) == (self.discount_cents is None):
            raise ValueError("exactly one discount field is required")
        if self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be after valid_from")
        return self


class CouponResponse(BaseModel):
    id: str
    code: str
    discount_pct: int | None
    discount_cents: int | None
    valid_from: datetime
    valid_until: datetime
    max_uses: int | None
    used_count: int
    created_at: datetime
