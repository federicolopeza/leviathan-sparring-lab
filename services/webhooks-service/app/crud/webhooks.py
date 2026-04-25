from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeliveryStatus, Webhook, WebhookDelivery
from app.models.base import now_utc


async def create_webhook(
    db: AsyncSession,
    *,
    user_id: str,
    url: str,
    events: list[str],
    secret_hash: str,
) -> Webhook:
    webhook = Webhook(user_id=user_id, url=url, events=events, secret_hash=secret_hash)
    db.add(webhook)
    await db.flush()
    return webhook


async def list_webhooks_for_user(db: AsyncSession, user_id: str) -> list[Webhook]:
    result = await db.execute(
        select(Webhook)
        .where(Webhook.user_id == user_id, Webhook.deleted_at.is_(None))
        .order_by(Webhook.created_at)
    )
    return list(result.scalars().all())


async def get_webhook_for_user(db: AsyncSession, webhook_id: str, user_id: str) -> Webhook | None:
    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.user_id == user_id,
            Webhook.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_dispatch_targets(
    db: AsyncSession,
    *,
    user_id: str,
    event_type: str,
) -> list[Webhook]:
    result = await db.execute(
        select(Webhook).where(
            Webhook.user_id == user_id,
            Webhook.deleted_at.is_(None),
        )
    )
    return [webhook for webhook in result.scalars().all() if event_type in webhook.events]


async def create_delivery(
    db: AsyncSession,
    *,
    webhook_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> WebhookDelivery:
    delivery = WebhookDelivery(
        webhook_id=webhook_id,
        event_type=event_type,
        payload=payload,
        status=DeliveryStatus.PENDING,
    )
    db.add(delivery)
    await db.flush()
    return delivery


async def get_delivery_with_webhook(
    db: AsyncSession,
    delivery_id: str,
) -> tuple[WebhookDelivery, Webhook] | None:
    result = await db.execute(
        select(WebhookDelivery, Webhook)
        .join(Webhook, Webhook.id == WebhookDelivery.webhook_id)
        .where(WebhookDelivery.id == delivery_id, Webhook.deleted_at.is_(None))
    )
    row = result.one_or_none()
    if row is None:
        return None
    delivery, webhook = row
    return delivery, webhook


async def list_deliveries_for_webhook(
    db: AsyncSession,
    webhook_id: str,
    *,
    limit: int,
    offset: int,
) -> list[WebhookDelivery]:
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


def soft_delete(webhook: Webhook) -> None:
    webhook.deleted_at = now_utc()
