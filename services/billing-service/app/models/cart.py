from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.coupon import Coupon
    from app.models.plan import Plan


class Cart(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "carts"

    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    org_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("plans.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    plan: Mapped[Plan] = relationship(back_populates="carts")
    coupons: Mapped[list[CartCoupon]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
    )


class CartCoupon(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "cart_coupons"

    cart_id: Mapped[str] = mapped_column(String(36), ForeignKey("carts.id"), index=True)
    coupon_id: Mapped[str] = mapped_column(String(36), ForeignKey("coupons.id"), index=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    cart: Mapped[Cart] = relationship(back_populates="coupons")
    coupon: Mapped[Coupon] = relationship(back_populates="cart_coupons")
