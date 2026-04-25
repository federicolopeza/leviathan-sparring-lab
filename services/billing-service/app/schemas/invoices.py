from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models import InvoiceStatus


class InvoiceResponse(BaseModel):
    id: str
    checkout_id: str
    user_id: str
    org_id: str
    number: str
    total_cents: int
    currency: str
    status: InvoiceStatus
    issued_at: datetime


class InvoiceListResponse(BaseModel):
    items: list[InvoiceResponse]
    page: int
    per_page: int
    total: int
