from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import OrgRole


class InvitationCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: OrgRole = OrgRole.MEMBER


class InvitationCreateResponse(BaseModel):
    invitation_id: str
    expires_at: datetime


class InvitationAcceptRequest(BaseModel):
    token: str = Field(min_length=1)


class InvitationPendingResponse(BaseModel):
    id: str
    email: str
    role: OrgRole
    expires_at: datetime
