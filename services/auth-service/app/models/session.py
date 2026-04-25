from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, now_utc

if TYPE_CHECKING:
    from app.models.user import User


class Session(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "sessions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
    user_agent: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="sessions")
