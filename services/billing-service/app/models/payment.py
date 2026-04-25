from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, now_utc

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class PaymentMethod(StrEnum):
    MOCK_CARD = "mock_card"


class PaymentStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Payment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "payments"

    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id"), index=True)
    method: Mapped[PaymentMethod] = mapped_column(
        SqlEnum(
            PaymentMethod,
            values_callable=lambda values: [value.value for value in values],
            native_enum=False,
            length=16,
        ),
        default=PaymentMethod.MOCK_CARD,
        nullable=False,
    )
    last4: Mapped[str] = mapped_column(String(4), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        SqlEnum(
            PaymentStatus,
            values_callable=lambda values: [value.value for value in values],
            native_enum=False,
            length=16,
        ),
        default=PaymentStatus.SUCCEEDED,
        nullable=False,
    )
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    invoice: Mapped[Invoice] = relationship(back_populates="payment")
