from __future__ import annotations

from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel

from app.models import UploadPurpose


class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    purpose: UploadPurpose
    size_bytes: int


class UploadListItem(BaseModel):
    upload_id: str
    filename: str
    purpose: UploadPurpose
    size_bytes: int
    mime_type: str
    sha256: str
    created_at: datetime


class AvatarFetchRequest(BaseModel):
    image_url: AnyHttpUrl


class AvatarFetchResponse(BaseModel):
    upload_id: str
    sha256: str
