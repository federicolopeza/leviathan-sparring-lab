from __future__ import annotations

import secrets
from time import perf_counter
from typing import Annotated

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.webhooks import (
    create_delivery,
    create_webhook,
    get_webhook_for_user,
    list_deliveries_for_webhook,
    list_dispatch_targets,
    list_webhooks_for_user,
    soft_delete,
)
from app.deps.auth import Principal, get_current_principal
from app.deps.db import get_db
from app.models import Webhook, WebhookDelivery
from app.schemas.webhooks import (
    DeliveryResponse,
    DispatchRequest,
    DispatchResponse,
    TestWebhookResponse,
    WebhookCreate,
    WebhookCreateResponse,
    WebhookResponse,
    WebhookUpdate,
)
from app.services.queue import webhook_queue
from app.services.signing import hash_secret, secret_id, signature_header
from app.services.url_validation import validate_webhook_url

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])
logger = structlog.get_logger()
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


def _webhook_response(webhook: Webhook) -> WebhookResponse:
    return WebhookResponse.model_validate(
        {
            "webhook_id": webhook.id,
            "url": webhook.url,
            "events": webhook.events,
            "created_at": webhook.created_at,
            "updated_at": webhook.updated_at,
        }
    )


def _delivery_response(delivery: WebhookDelivery) -> DeliveryResponse:
    return DeliveryResponse.model_validate(
        {
            "id": delivery.id,
            "webhook_id": delivery.webhook_id,
            "event_type": delivery.event_type,
            "payload": delivery.payload,
            "status": delivery.status,
            "attempt_count": delivery.attempt_count,
            "last_attempted_at": delivery.last_attempted_at,
            "next_retry_at": delivery.next_retry_at,
            "response_status": delivery.response_status,
            "response_body_preview": delivery.response_body_preview,
            "created_at": delivery.created_at,
        }
    )


async def _require_webhook(db: AsyncSession, webhook_id: str, user_id: str) -> Webhook:
    webhook = await get_webhook_for_user(db, webhook_id, user_id)
    if webhook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return webhook


@router.post("", response_model=WebhookCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user_webhook(
    payload: WebhookCreate,
    principal: CurrentPrincipal,
    db: DbSession,
) -> WebhookCreateResponse:
    url = validate_webhook_url(payload.url)
    raw_secret = payload.secret or secrets.token_urlsafe(32)
    stored_secret_hash = hash_secret(raw_secret)
    webhook = await create_webhook(
        db,
        user_id=principal.user.id,
        url=url,
        events=payload.events,
        secret_hash=stored_secret_hash,
    )
    await db.commit()
    await db.refresh(webhook)
    logger.info(
        "webhook_secret_issued",
        webhook_id=webhook.id,
        secret_id=secret_id(stored_secret_hash),
    )
    return WebhookCreateResponse(
        webhook_id=webhook.id,
        url=webhook.url,
        events=webhook.events,
        secret=raw_secret,
    )


@router.get("", response_model=list[WebhookResponse])
async def list_user_webhooks(
    principal: CurrentPrincipal,
    db: DbSession,
) -> list[WebhookResponse]:
    webhooks = await list_webhooks_for_user(db, principal.user.id)
    return [_webhook_response(webhook) for webhook in webhooks]


@router.post("/_internal/dispatch", response_model=DispatchResponse)
async def dispatch_webhook_event(
    payload: DispatchRequest,
    principal: CurrentPrincipal,
    db: DbSession,
) -> DispatchResponse:
    if not principal.user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not Found")
    targets = await list_dispatch_targets(
        db,
        user_id=payload.target_user_id,
        event_type=payload.event_type,
    )
    delivery_ids: list[str] = []
    for webhook in targets:
        delivery = await create_delivery(
            db,
            webhook_id=webhook.id,
            event_type=payload.event_type,
            payload=payload.payload,
        )
        delivery_ids.append(delivery.id)
        webhook_queue.enqueue(delivery.id)
    await db.commit()
    return DispatchResponse(enqueued=len(delivery_ids), delivery_ids=delivery_ids)


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def patch_user_webhook(
    webhook_id: str,
    payload: WebhookUpdate,
    principal: CurrentPrincipal,
    db: DbSession,
) -> WebhookResponse:
    webhook = await _require_webhook(db, webhook_id, principal.user.id)
    updates = payload.model_dump(exclude_unset=True)
    if "url" in updates and updates["url"] is not None:
        webhook.url = validate_webhook_url(updates["url"])
    if "events" in updates and updates["events"] is not None:
        webhook.events = updates["events"]
    await db.commit()
    await db.refresh(webhook)
    return _webhook_response(webhook)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_webhook(
    webhook_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> Response:
    webhook = await _require_webhook(db, webhook_id, principal.user.id)
    soft_delete(webhook)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{webhook_id}/test", response_model=TestWebhookResponse)
async def test_user_webhook(
    webhook_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
) -> TestWebhookResponse:
    webhook = await _require_webhook(db, webhook_id, principal.user.id)
    body = {"event_type": "webhook.test", "payload": {"webhook_id": webhook.id}}
    headers = {"x-melispy-signature": signature_header(body, webhook.secret_hash)}
    started = perf_counter()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(webhook.url, json=body, headers=headers)
        status_code = response.status_code
        body_preview = response.text[:512]
    except httpx.HTTPError as exc:
        status_code = 0
        body_preview = str(exc)[:512]
    duration_ms = int((perf_counter() - started) * 1000)
    return TestWebhookResponse(
        status_code=status_code,
        duration_ms=duration_ms,
        body_preview=body_preview,
    )


@router.get("/{webhook_id}/deliveries", response_model=list[DeliveryResponse])
async def list_webhook_deliveries(
    webhook_id: str,
    principal: CurrentPrincipal,
    db: DbSession,
    limit: int = 50,
    offset: int = 0,
) -> list[DeliveryResponse]:
    webhook = await _require_webhook(db, webhook_id, principal.user.id)
    bounded_limit = max(1, min(limit, 100))
    bounded_offset = max(0, offset)
    deliveries = await list_deliveries_for_webhook(
        db,
        webhook.id,
        limit=bounded_limit,
        offset=bounded_offset,
    )
    return [_delivery_response(delivery) for delivery in deliveries]
