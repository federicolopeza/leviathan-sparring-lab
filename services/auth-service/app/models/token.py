from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class TokenBase(UUIDPrimaryKeyMixin):
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PasswordResetToken(TokenBase, Base):
    __tablename__ = "password_reset_tokens"


class EmailVerifyToken(TokenBase, Base):
    __tablename__ = "email_verify_tokens"


class MagicLinkToken(TokenBase, Base):
    __tablename__ = "magic_link_tokens"
