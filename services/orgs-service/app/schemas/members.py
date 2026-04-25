from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import OrgRole


class MemberCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=36)
    role: OrgRole = OrgRole.MEMBER


class MemberResponse(BaseModel):
    id: str
    org_id: str
    user_id: str
    role: OrgRole
    created_at: datetime
