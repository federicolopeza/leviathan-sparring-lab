from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, now_utc


class NotificationTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notification_templates"

    code: Mapped[str] = mapped_column(String(64), index=True, unique=True, nullable=False)
    subject_template: Mapped[str] = mapped_column(String(240), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    locale: Mapped[str] = mapped_column(String(2), nullable=False, default="es")


class NotificationDispatch(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notification_dispatches"

    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    template_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("notification_templates.id"),
        nullable=False,
    )
    vars: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
