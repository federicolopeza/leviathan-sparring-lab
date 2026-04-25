from __future__ import annotations

import hashlib
import os
from typing import Annotated
from uuid import uuid4

import anyio
import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Principal, get_current_principal
from app.config import get_settings
from app.database import get_db
from app.minio_client import MinIOClient, get_minio_client
from app.models import Upload, UploadPurpose
from app.schemas import AvatarFetchRequest, AvatarFetchResponse, UploadListItem, UploadResponse

router = APIRouter(prefix="/v1/uploads", tags=["uploads"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]
ObjectStore = Annotated[MinIOClient, Depends(get_minio_client)]
UploadFilePart = Annotated[UploadFile, File(...)]
UploadPurposeForm = Annotated[UploadPurpose, Form(...)]

MAGIC_TYPES: tuple[tuple[bytes, str], ...] = (
    (bytes.fromhex("FFD8FF"), "image/jpeg"),
    (bytes.fromhex("89504E47"), "image/png"),
    (bytes.fromhex("52494646"), "image/webp"),
    (bytes.fromhex("25504446"), "application/pdf"),
    (bytes.fromhex("504B0304"), "application/zip"),
)


def _sniff_mime(data: bytes) -> str | None:
    for magic, mime_type in MAGIC_TYPES:
        if data.startswith(magic):
            return mime_type
    return None


def _upload_response(upload: Upload) -> UploadResponse:
    return UploadResponse(
        upload_id=upload.id,
        filename=upload.original_filename,
        purpose=upload.purpose,
        size_bytes=upload.size_bytes,
    )


def _upload_list_item(upload: Upload) -> UploadListItem:
    return UploadListItem(
        upload_id=upload.id,
        filename=upload.original_filename,
        purpose=upload.purpose,
        size_bytes=upload.size_bytes,
        mime_type=upload.mime_type,
        sha256=upload.sha256,
        created_at=upload.created_at,
    )


def _build_storage_key(user_id: str, original_filename: str) -> str:
    return f"uploads/{user_id}/{uuid4()}-{original_filename}"


async def _store_upload(
    *,
    db: AsyncSession,
    object_store: MinIOClient,
    user_id: str,
    purpose: UploadPurpose,
    original_filename: str,
    data: bytes,
    mime_type: str,
) -> Upload:
    upload = Upload(
        user_id=user_id,
        purpose=purpose,
        original_filename=original_filename,
        storage_key=_build_storage_key(user_id, original_filename),
        mime_type=mime_type,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )
    await object_store.put_object(upload.storage_key, data, mime_type)
    db.add(upload)
    await db.commit()
    await db.refresh(upload)
    return upload


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def create_upload(
    principal: CurrentPrincipal,
    db: DbSession,
    object_store: ObjectStore,
    file: UploadFilePart,
    purpose: UploadPurposeForm,
) -> UploadResponse:
    settings = get_settings()
    head = await file.read(16)
    # V-T4-006 INTENTIONAL VULN: polyglot accepted.
    # JPEG magic header + PHP payload after EXIF passes magic check.
    mime_type = _sniff_mime(head)
    if mime_type is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid file")
    remainder = await file.read()
    data = head + remainder
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Too large",
        )
    upload = await _store_upload(
        db=db,
        object_store=object_store,
        user_id=principal.user_id,
        purpose=purpose,
        original_filename=file.filename or "upload.bin",
        data=data,
        mime_type=mime_type,
    )
    return _upload_response(upload)


@router.get("", response_model=list[UploadListItem])
async def list_uploads(principal: CurrentPrincipal, db: DbSession) -> list[UploadListItem]:
    result = await db.execute(
        select(Upload).where(Upload.user_id == principal.user_id).order_by(Upload.created_at.desc())
    )
    return [_upload_list_item(upload) for upload in result.scalars().all()]


@router.get("/{filename:path}")
async def get_upload(filename: str, principal: CurrentPrincipal) -> FileResponse:
    settings = get_settings()
    _ = principal
    # V-T4-005 INTENTIONAL VULN: filename joined without sanitize -> path traversal
    path = os.path.join(settings.MINIO_LOCAL_CACHE_DIR, filename)
    if not await anyio.Path(path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return FileResponse(path, media_type="application/octet-stream")


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_upload(
    upload_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
    object_store: ObjectStore,
) -> None:
    result = await db.execute(
        select(Upload).where(Upload.id == upload_id, Upload.user_id == principal.user_id)
    )
    upload = result.scalar_one_or_none()
    if upload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    await object_store.delete_object(upload.storage_key)
    await db.delete(upload)
    await db.commit()


@router.post(
    "/avatar-fetch",
    response_model=AvatarFetchResponse,
    status_code=status.HTTP_201_CREATED,
)
async def avatar_fetch(
    payload: AvatarFetchRequest,
    principal: CurrentPrincipal,
    db: DbSession,
    object_store: ObjectStore,
) -> AvatarFetchResponse:
    async with httpx.AsyncClient() as client:
        # V-T4-003 INTENTIONAL VULN: SSRF.
        # No IP allowlist, no scheme check beyond http/https.
        # Allows metadata and internal hosts.
        response = await client.get(str(payload.image_url))
    response.raise_for_status()
    data = response.content
    settings = get_settings()
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Too large",
        )
    mime_type = _sniff_mime(data[:16]) or "application/octet-stream"
    upload = await _store_upload(
        db=db,
        object_store=object_store,
        user_id=principal.user_id,
        purpose=UploadPurpose.AVATAR,
        original_filename=os.path.basename(str(payload.image_url)) or "avatar-fetch",
        data=data,
        mime_type=mime_type,
    )
    return AvatarFetchResponse(upload_id=upload.id, sha256=upload.sha256)
