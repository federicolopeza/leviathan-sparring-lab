from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Invoice, InvoiceStatus, Payment, PaymentMethod, PaymentStatus


async def create_paid_invoice(
    db: AsyncSession,
    *,
    checkout_id: str,
    user_id: str,
    org_id: str,
    total_cents: int,
    currency: str,
) -> Invoice:
    number = await next_invoice_number(db)
    invoice = Invoice(
        checkout_id=checkout_id,
        user_id=user_id,
        org_id=org_id,
        number=number,
        total_cents=total_cents,
        currency=currency,
        status=InvoiceStatus.PAID,
    )
    db.add(invoice)
    await db.flush()
    payment = Payment(
        invoice_id=invoice.id,
        method=PaymentMethod.MOCK_CARD,
        last4="4242",
        status=PaymentStatus.SUCCEEDED,
    )
    db.add(payment)
    await db.flush()
    return invoice


async def next_invoice_number(db: AsyncSession) -> str:
    today = datetime.now(UTC).strftime("%Y%m%d")
    result = await db.execute(select(func.count()).select_from(Invoice))
    seq = int(result.scalar_one()) + 1
    return f"INV-{today}-{seq:06d}"


async def get_invoice(db: AsyncSession, invoice_id: str) -> Invoice | None:
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    return result.scalar_one_or_none()


async def list_user_invoices(
    db: AsyncSession,
    *,
    user_id: str,
    page: int,
    per_page: int,
) -> tuple[list[Invoice], int]:
    count_result = await db.execute(
        select(func.count()).select_from(Invoice).where(Invoice.user_id == user_id)
    )
    total = int(count_result.scalar_one())
    result = await db.execute(
        select(Invoice)
        .where(Invoice.user_id == user_id)
        .order_by(Invoice.issued_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    return list(result.scalars().all()), total
