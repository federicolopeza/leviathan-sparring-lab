from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | dict[str, JsonValue] | list[JsonValue]


class EmailDispatchRequest(BaseModel):
    to: str
    template_id: str
    vars: dict[str, JsonValue] = Field(default_factory=dict)


class EmailDispatchResponse(BaseModel):
    queued: bool
    template_id: str
    to: str


class NotificationTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    subject_template: str
    body_template: str
    locale: str
    updated_at: datetime


class InvoicePdfRequest(BaseModel):
    invoice_id: str
    invoice_number: str


class InvoicePdfResponse(BaseModel):
    invoice_id: str
    output_path: str


class AvatarProcessRequest(BaseModel):
    upload_id: str


class AvatarProcessResponse(BaseModel):
    upload_id: str
    output_path: str


class DispatchEventRequest(BaseModel):
    event_type: str
    target_user_id: str
    payload: dict[str, JsonValue] = Field(default_factory=dict)


class DispatchEventResponse(BaseModel):
    dispatched: bool
    template_id: str
