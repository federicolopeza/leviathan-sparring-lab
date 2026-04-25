from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    org_name: str = Field(min_length=1, max_length=200)


class SignupResponse(BaseModel):
    user_id: str
    email_verify_required: bool = True


class VerifyRequest(BaseModel):
    token: str = Field(min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    email_verified: bool
    is_admin: bool


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: UserResponse


class ForgotRequest(BaseModel):
    email: EmailStr


class ResetRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=256)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class SessionResponse(BaseModel):
    session_id: str
    ip: str
    user_agent: str
    created_at: datetime
    last_seen_at: datetime
