from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.checkout import Checkout


class PlanCode(StrEnum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Plan(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "plans"

    code: Mapped[PlanCode] = mapped_column(
        SqlEnum(
            PlanCode,
            values_callable=lambda values: [value.value for value in values],
            native_enum=False,
            length=32,
        ),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    monthly_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    features: Mapped[dict[str, object]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )

    carts: Mapped[list[Cart]] = relationship(back_populates="plan")
    checkouts: Mapped[list[Checkout]] = relationship(back_populates="plan")
