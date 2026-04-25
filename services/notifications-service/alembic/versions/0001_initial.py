"""Initial notifications service schema."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_templates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("subject_template", sa.String(length=240), nullable=False),
        sa.Column("body_template", sa.Text(), nullable=False),
        sa.Column("locale", sa.String(length=2), nullable=False, server_default="es"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "notification_dispatches",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column(
            "template_id",
            sa.String(length=36),
            sa.ForeignKey("notification_templates.id"),
            nullable=False,
        ),
        sa.Column("vars", sa.JSON(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_notification_templates_code",
        "notification_templates",
        ["code"],
        unique=True,
    )
    op.create_index(
        "ix_notification_dispatches_user_id",
        "notification_dispatches",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_notification_dispatches_user_id", table_name="notification_dispatches")
    op.drop_index("ix_notification_templates_code", table_name="notification_templates")
    op.drop_table("notification_dispatches")
    op.drop_table("notification_templates")
