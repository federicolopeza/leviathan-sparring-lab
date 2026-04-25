from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.invoice import Invoice
    from app.models.plan import Plan


class CheckoutStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Checkout(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "checkouts"

    cart_id: Mapped[str] = mapped_column(String(36), ForeignKey("carts.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    org_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("plans.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[CheckoutStatus] = mapped_column(
        SqlEnum(
            CheckoutStatus,
            values_callable=lambda values: [value.value for value in values],
            native_enum=False,
            length=16,
        ),
        default=CheckoutStatus.PENDING,
        nullable=False,
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    cart: Mapped[Cart] = relationship()
    plan: Mapped[Plan] = relationship(back_populates="checkouts")
    invoice: Mapped[Invoice | None] = relationship(back_populates="checkout")
