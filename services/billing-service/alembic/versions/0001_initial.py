"""Initial billing service schema."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("monthly_price_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("features", sa.JSON(), nullable=False),
    )
    op.create_table(
        "coupons",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("discount_pct", sa.Integer(), nullable=True),
        sa.Column("discount_cents", sa.Integer(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "carts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("org_id", sa.String(length=36), nullable=False),
        sa.Column("plan_id", sa.String(length=36), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "cart_coupons",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("cart_id", sa.String(length=36), sa.ForeignKey("carts.id"), nullable=False),
        sa.Column("coupon_id", sa.String(length=36), sa.ForeignKey("coupons.id"), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "checkouts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("cart_id", sa.String(length=36), sa.ForeignKey("carts.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("org_id", sa.String(length=36), nullable=False),
        sa.Column("plan_id", sa.String(length=36), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("subtotal_cents", sa.Integer(), nullable=False),
        sa.Column("discount_cents", sa.Integer(), nullable=False),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("idempotency_key", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "checkout_id",
            sa.String(length=36),
            sa.ForeignKey("checkouts.id"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("org_id", sa.String(length=36), nullable=False),
        sa.Column("number", sa.String(length=32), nullable=False),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="paid"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("invoice_id", sa.String(length=36), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("method", sa.String(length=16), nullable=False, server_default="mock_card"),
        sa.Column("last4", sa.String(length=4), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="succeeded"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_plans_code", "plans", ["code"], unique=True)
    op.create_index("ix_coupons_code", "coupons", ["code"], unique=True)
    op.create_index("ix_carts_user_id", "carts", ["user_id"])
    op.create_index("ix_carts_org_id", "carts", ["org_id"])
    op.create_index("ix_cart_coupons_cart_id", "cart_coupons", ["cart_id"])
    op.create_index("ix_cart_coupons_coupon_id", "cart_coupons", ["coupon_id"])
    op.create_index("ix_checkouts_cart_id", "checkouts", ["cart_id"])
    op.create_index("ix_checkouts_user_id", "checkouts", ["user_id"])
    op.create_index("ix_checkouts_org_id", "checkouts", ["org_id"])
    op.create_index("ix_invoices_checkout_id", "invoices", ["checkout_id"])
    op.create_index("ix_invoices_user_id", "invoices", ["user_id"])
    op.create_index("ix_invoices_org_id", "invoices", ["org_id"])
    op.create_index("ix_invoices_number", "invoices", ["number"])
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"])


def downgrade() -> None:
    op.drop_index("ix_payments_invoice_id", table_name="payments")
    op.drop_index("ix_invoices_number", table_name="invoices")
    op.drop_index("ix_invoices_org_id", table_name="invoices")
    op.drop_index("ix_invoices_user_id", table_name="invoices")
    op.drop_index("ix_invoices_checkout_id", table_name="invoices")
    op.drop_index("ix_checkouts_org_id", table_name="checkouts")
    op.drop_index("ix_checkouts_user_id", table_name="checkouts")
    op.drop_index("ix_checkouts_cart_id", table_name="checkouts")
    op.drop_index("ix_cart_coupons_coupon_id", table_name="cart_coupons")
    op.drop_index("ix_cart_coupons_cart_id", table_name="cart_coupons")
    op.drop_index("ix_carts_org_id", table_name="carts")
    op.drop_index("ix_carts_user_id", table_name="carts")
    op.drop_index("ix_coupons_code", table_name="coupons")
    op.drop_index("ix_plans_code", table_name="plans")
    op.drop_table("payments")
    op.drop_table("invoices")
    op.drop_table("checkouts")
    op.drop_table("cart_coupons")
    op.drop_table("carts")
    op.drop_table("coupons")
    op.drop_table("plans")
