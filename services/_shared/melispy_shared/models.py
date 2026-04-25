"""Shared SQLAlchemy models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    """Declarative base for all Melispy service models."""


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class UUIDPKMixin:
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)


class TenantMixin:
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)


class AuditLog(UUIDPKMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(200), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(
        MutableDict.as_mutable(JSON().with_variant(JSONB, "postgresql")),
        default=dict,
        nullable=False,
    )
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    hmac: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    @declared_attr.directive
    @classmethod
    def __table_args__(cls) -> tuple[Index]:
        return (Index("ix_audit_logs_tenant_ts", "tenant_id", "ts"),)
