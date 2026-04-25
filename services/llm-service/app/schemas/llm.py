from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models import MessageRole


class ConversationCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    model: str = Field(default="melispy-fixture-1", min_length=1, max_length=80)


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    model: str
    created_at: datetime


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    created_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse]


class MessageCreateRequest(BaseModel):
    role: MessageRole = MessageRole.USER
    content: str = Field(min_length=1)


class MessageCreateResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


class TokenVerifyRequest(BaseModel):
    token: str = Field(min_length=1)
