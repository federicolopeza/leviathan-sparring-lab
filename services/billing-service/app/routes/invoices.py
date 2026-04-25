from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.invoices import get_invoice, list_user_invoices
from app.deps.auth import Principal, get_current_principal
from app.deps.db import get_db
from app.models import Invoice
from app.schemas.invoices import InvoiceListResponse, InvoiceResponse

router = APIRouter(prefix="/v1/billing/invoices", tags=["billing-invoices"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


def invoice_response(invoice: Invoice) -> InvoiceResponse:
    return InvoiceResponse.model_validate(
        {
            "id": invoice.id,
            "checkout_id": invoice.checkout_id,
            "user_id": invoice.user_id,
            "org_id": invoice.org_id,
            "number": invoice.number,
            "total_cents": invoice.total_cents,
            "currency": invoice.currency,
            "status": invoice.status,
            "issued_at": invoice.issued_at,
        }
    )


@router.get("", response_model=InvoiceListResponse)
async def get_invoices(
    principal: CurrentPrincipal,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> InvoiceListResponse:
    invoices, total = await list_user_invoices(
        db,
        user_id=principal.user_id,
        page=page,
        per_page=per_page,
    )
    return InvoiceListResponse(
        items=[invoice_response(invoice) for invoice in invoices],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice_by_id(
    invoice_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> InvoiceResponse:
    invoice = await get_invoice(db, invoice_id)
    if invoice is None or invoice.user_id != principal.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return invoice_response(invoice)
