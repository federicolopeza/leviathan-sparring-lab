from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, now_utc

if TYPE_CHECKING:
    from app.models.checkout import Checkout
    from app.models.payment import Payment


class InvoiceStatus(StrEnum):
    PAID = "paid"
    REFUNDED = "refunded"


class Invoice(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "invoices"

    checkout_id: Mapped[str] = mapped_column(String(36), ForeignKey("checkouts.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    org_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    number: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        SqlEnum(
            InvoiceStatus,
            values_callable=lambda values: [value.value for value in values],
            native_enum=False,
            length=16,
        ),
        default=InvoiceStatus.PAID,
        nullable=False,
    )
    issued_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=now_utc)

    checkout: Mapped[Checkout] = relationship(back_populates="invoice")
    payment: Mapped[Payment | None] = relationship(back_populates="invoice")
