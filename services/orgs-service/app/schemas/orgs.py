from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import OrgPlan


class OrgCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    plan: OrgPlan = OrgPlan.FREE
    region: str = Field(default="sa-east-1", min_length=1, max_length=16)


class OrgUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    plan: OrgPlan | None = None
    region: str | None = Field(default=None, min_length=1, max_length=16)


class OrgResponse(BaseModel):
    id: str
    name: str
    plan: OrgPlan
    region: str
    owner_user_id: str
    created_at: datetime
    updated_at: datetime


class OrgDetailResponse(OrgResponse):
    member_count: int
