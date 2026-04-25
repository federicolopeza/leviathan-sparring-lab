from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.invitation import OrgInvitation
    from app.models.membership import OrgMembership


class OrgPlan(StrEnum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Org(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orgs"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    plan: Mapped[OrgPlan] = mapped_column(
        SqlEnum(
            OrgPlan,
            values_callable=lambda values: [value.value for value in values],
            native_enum=False,
            length=16,
        ),
        default=OrgPlan.FREE,
        nullable=False,
    )
    region: Mapped[str] = mapped_column(String(16), default="sa-east-1", nullable=False)
    owner_user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    memberships: Mapped[list[OrgMembership]] = relationship(
        back_populates="org",
        cascade="all, delete-orphan",
    )
    invitations: Mapped[list[OrgInvitation]] = relationship(
        back_populates="org",
        cascade="all, delete-orphan",
    )
