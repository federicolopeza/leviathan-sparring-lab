from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import AgentRunStatus


class AgentRunCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    input_json: dict[str, object] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    id: str
    user_id: str
    org_id: str | None
    name: str
    status: AgentRunStatus
    input_json: dict[str, object]
    output_json: dict[str, object] | None
    error_msg: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentRunRenderResponse(BaseModel):
    run_id: str
    rendered: str
