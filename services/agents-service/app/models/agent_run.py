from __future__ import annotations

from enum import StrEnum

from sqlalchemy import JSON, String, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AgentRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_runs"

    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    org_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[AgentRunStatus] = mapped_column(
        SqlEnum(
            AgentRunStatus,
            values_callable=lambda values: [value.value for value in values],
            native_enum=False,
            length=16,
        ),
        default=AgentRunStatus.QUEUED,
        index=True,
        nullable=False,
    )
    input_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    output_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
