from __future__ import annotations

import json
import subprocess  # noqa: S404
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.deps.auth import Principal, get_current_principal, require_admin_or_service
from app.models import NotificationDispatch, NotificationTemplate
from app.schemas import (
    AvatarProcessRequest,
    AvatarProcessResponse,
    DispatchEventRequest,
    DispatchEventResponse,
    EmailDispatchRequest,
    EmailDispatchResponse,
    InvoicePdfRequest,
    InvoicePdfResponse,
    NotificationTemplateResponse,
)
from app.services.minio_client import MinIOClient, get_minio_client
from app.services.templates import get_template_by_code, render_template

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]
ObjectStore = Annotated[MinIOClient, Depends(get_minio_client)]


async def _authorized_principal(principal: CurrentPrincipal) -> Principal:
    return await require_admin_or_service(principal)


AuthorizedPrincipal = Annotated[Principal, Depends(_authorized_principal)]


async def _render_and_dispatch(
    *,
    db: AsyncSession,
    to: str,
    template_code: str,
    vars: dict[str, object],
    user_id: str,
) -> EmailDispatchResponse:
    template = await get_template_by_code(db, template_code)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    subject, body = render_template(template, vars)
    settings = get_settings()
    print(
        json.dumps(
            {
                "smtp_log_only": settings.SMTP_LOG_ONLY,
                "from": settings.SMTP_FROM,
                "to": to,
                "template_id": template_code,
                "subject": subject,
                "body": body,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    db.add(
        NotificationDispatch(
            user_id=user_id,
            template_id=template.id,
            vars=vars,
            error=None,
        )
    )
    await db.commit()
    return EmailDispatchResponse(queued=True, template_id=template_code, to=to)


@router.post("/email", response_model=EmailDispatchResponse)
async def send_email(
    payload: EmailDispatchRequest,
    principal: AuthorizedPrincipal,
    db: DbSession,
) -> EmailDispatchResponse:
    return await _render_and_dispatch(
        db=db,
        to=payload.to,
        template_code=payload.template_id,
        vars=dict(payload.vars),
        user_id=principal.user_id,
    )


@router.get("/templates", response_model=list[NotificationTemplateResponse])
async def list_templates(
    _principal: AuthorizedPrincipal,
    db: DbSession,
) -> list[NotificationTemplate]:
    result = await db.execute(select(NotificationTemplate).order_by(NotificationTemplate.code))
    return list(result.scalars().all())


@router.post("/invoice-pdf", response_model=InvoicePdfResponse)
async def invoice_pdf(
    payload: InvoicePdfRequest,
    _principal: AuthorizedPrincipal,
) -> InvoicePdfResponse:
    settings = get_settings()
    output_path = "out.pdf"
    # VULN V-T6-007: CWE-78 OS Command Injection — invoice_number unsanitized
    command = f"{settings.WKHTMLTOPDF_BIN} invoice-{payload.invoice_number}.html {output_path}"
    subprocess.run(command, shell=True, check=False)  # noqa: ASYNC221,S602
    return InvoicePdfResponse(invoice_id=payload.invoice_id, output_path=output_path)


@router.post("/avatar-process", response_model=AvatarProcessResponse)
async def avatar_process(
    payload: AvatarProcessRequest,
    _principal: AuthorizedPrincipal,
    object_store: ObjectStore,
) -> AvatarProcessResponse:
    settings = get_settings()
    svg_data = await object_store.get_object(payload.upload_id)
    svg_text = svg_data.decode("utf-8", errors="ignore")
    work_dir = Path(settings.MINIO_LOCAL_CACHE_DIR) / "avatar-processing"
    work_dir.mkdir(parents=True, exist_ok=True)
    input_path = work_dir / "input.svg"
    output_path = work_dir / "out.png"
    input_path.write_bytes(svg_data)
    # VULN V-T6-006: CWE-78 ImageMagick delegate injection — no policy sandbox (CVE-2016-3714)
    command = f"{settings.MAGICK_BIN} convert {svg_text} {output_path}"
    subprocess.run(command, shell=True, check=False)  # noqa: ASYNC221,S602
    return AvatarProcessResponse(upload_id=payload.upload_id, output_path=str(output_path))


@router.post("/dispatch-event", response_model=DispatchEventResponse)
async def dispatch_event(
    payload: DispatchEventRequest,
    principal: AuthorizedPrincipal,
    db: DbSession,
) -> DispatchEventResponse:
    template_id = str(payload.payload.get("template_id") or payload.event_type)
    if await get_template_by_code(db, template_id) is None:
        template_id = "welcome"
    to = str(payload.payload.get("to") or f"{payload.target_user_id}@melispy.local")
    vars_payload = payload.payload.get("vars")
    vars = vars_payload if isinstance(vars_payload, dict) else payload.payload
    await _render_and_dispatch(
        db=db,
        to=to,
        template_code=template_id,
        vars=dict(vars),
        user_id=principal.user_id,
    )
    return DispatchEventResponse(dispatched=True, template_id=template_id)
