from __future__ import annotations

from datetime import datetime

from pydantic import AnyUrl, BaseModel, EmailStr, Field


class UserProfileUpdate(BaseModel):
    # avatar_url is intentionally NOT here — must go through POST /me/avatar which validates
    # scheme + extension. Skipping that gate via PATCH would bypass Phase 1 SAFE checks.
    name: str | None = Field(default=None, min_length=1, max_length=200)
    bio: str | None = Field(default=None, max_length=10_000)


class UserOut(BaseModel):
    id: str
    email: EmailStr | None = None
    name: str
    bio: str | None
    avatar_url: str | None
    is_admin: bool | None = None
    created_at: datetime


class AvatarIn(BaseModel):
    image_url: AnyUrl
