from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class UserSummary(BaseModel):
    id: str
    email: str
    name: str
    is_admin: bool
    created_at: datetime
    last_seen_at: datetime | None


class UserListResponse(BaseModel):
    items: list[UserSummary]
    page: int
    per_page: int
    total: int


class UserDetail(UserSummary):
    bio: str
    deleted_at: datetime | None


class AuditLogResponse(BaseModel):
    id: str
    ts: datetime
    event_type: str
    actor_id: str
    resource: str
    action: str
    payload: dict[str, object]
    prev_hash: str
    hmac: str


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    page: int
    per_page: int
    total: int
    chain_valid: bool
    chain_badge: str


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(min_length=1)


class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    scopes: list[str]
    key: str
    created_at: datetime


class ApiKeyResponse(BaseModel):
    id: str
    user_id: str
    name: str
    scopes: list[str]
    created_at: datetime
    revoked_at: datetime | None


class BrandingRequest(BaseModel):
    welcome_message: str = Field(min_length=1)


class BrandingResponse(BaseModel):
    id: str | None
    welcome_message: str
    rendered_html: str
    updated_by_user_id: str | None
    updated_at: datetime | None


class InternalActionRequest(BaseModel):
    action: Literal["revoke_session", "rotate_jwt_key", "dump_audit"]


class InternalActionResponse(BaseModel):
    status: str
    actor_user_id: str
    action: str
