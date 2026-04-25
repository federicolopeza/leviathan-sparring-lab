from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models import DeliveryStatus


class WebhookCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    events: list[str] = Field(min_length=1, max_length=32)
    secret: str | None = Field(default=None, min_length=16, max_length=256)


class WebhookUpdate(BaseModel):
    url: str | None = Field(default=None, min_length=1, max_length=2048)
    events: list[str] | None = Field(default=None, min_length=1, max_length=32)


class WebhookResponse(BaseModel):
    webhook_id: str
    url: str
    events: list[str]
    created_at: datetime
    updated_at: datetime


class WebhookCreateResponse(BaseModel):
    webhook_id: str
    url: str
    events: list[str]
    secret: str


class TestWebhookResponse(BaseModel):
    status_code: int
    duration_ms: int
    body_preview: str


class DeliveryResponse(BaseModel):
    id: str
    webhook_id: str
    event_type: str
    payload: dict[str, Any]
    status: DeliveryStatus
    attempt_count: int
    last_attempted_at: datetime | None
    next_retry_at: datetime | None
    response_status: int | None
    response_body_preview: str | None
    created_at: datetime


class DispatchRequest(BaseModel):
    event_type: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]
    target_user_id: str = Field(min_length=1, max_length=36)


class DispatchResponse(BaseModel):
    enqueued: int
    delivery_ids: list[str]
