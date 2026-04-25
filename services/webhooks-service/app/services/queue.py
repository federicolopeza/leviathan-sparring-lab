from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import httpx
from app.config import get_settings
from app.crud.webhooks import get_delivery_with_webhook
from app.models import DeliveryStatus, Webhook, WebhookDelivery
from app.services.signing import canonical_body, signature_header
from sqlalchemy.ext.asyncio import AsyncSession


class WebhookQueue:
    def __init__(self) -> None:
        self._delivery_ids: list[str] = []

    def clear(self) -> None:
        self._delivery_ids.clear()

    def enqueue(self, delivery_id: str) -> None:
        self._delivery_ids.append(delivery_id)

    async def process_next(
        self,
        db: AsyncSession,
        *,
        client: httpx.AsyncClient | None = None,
        force: bool = False,
    ) -> WebhookDelivery | None:
        if not self._delivery_ids:
            return None
        delivery_id = self._delivery_ids.pop(0)
        row = await get_delivery_with_webhook(db, delivery_id)
        if row is None:
            return None
        delivery, webhook = row
        now = datetime.now(UTC)
        if delivery.next_retry_at is not None and delivery.next_retry_at > now and not force:
            self.enqueue(delivery_id)
            return None
        await self._deliver(db, delivery, webhook, client=client)
        return delivery

    async def drain(
        self,
        db: AsyncSession,
        *,
        client: httpx.AsyncClient | None = None,
        force: bool = False,
        max_iterations: int = 100,
    ) -> list[WebhookDelivery]:
        processed: list[WebhookDelivery] = []
        for _ in range(max_iterations):
            delivery = await self.process_next(db, client=client, force=force)
            if delivery is None:
                break
            processed.append(delivery)
        return processed

    async def _deliver(
        self,
        db: AsyncSession,
        delivery: WebhookDelivery,
        webhook: Webhook,
        *,
        client: httpx.AsyncClient | None,
    ) -> None:
        settings = get_settings()
        now = datetime.now(UTC)
        event_id = str(uuid4())  # V-T4-010 INTENTIONAL VULN: event_id regenerated per attempt — receivers cannot dedup, duplicate delivery on flap  # noqa: E501
        body = {
            "event_id": event_id,
            "event_type": delivery.event_type,
            "payload": delivery.payload,
            "created_at": now.isoformat(),
        }
        headers = {
            "content-type": "application/json",
            "x-melispy-signature": signature_header(body, webhook.secret_hash),
        }
        owns_client = client is None
        active_client = client or httpx.AsyncClient(timeout=5.0)
        try:
            response = await active_client.post(
                webhook.url,
                content=canonical_body(body),
                headers=headers,
            )
            delivery.response_status = response.status_code
            delivery.response_body_preview = response.text[:512]
            succeeded = 200 <= response.status_code < 300
        except httpx.HTTPError as exc:
            delivery.response_status = None
            delivery.response_body_preview = str(exc)[:512]
            succeeded = False
        finally:
            if owns_client:
                await active_client.aclose()

        delivery.attempt_count += 1
        delivery.last_attempted_at = now
        if succeeded:
            delivery.status = DeliveryStatus.SUCCEEDED
            delivery.next_retry_at = None
        elif delivery.attempt_count >= settings.MAX_RETRY_ATTEMPTS:
            delivery.status = DeliveryStatus.FAILED
            delivery.next_retry_at = None
        else:
            delivery.status = DeliveryStatus.PENDING
            backoff_ms = settings.INITIAL_BACKOFF_MS * (2 ** (delivery.attempt_count - 1))
            delivery.next_retry_at = now + timedelta(milliseconds=backoff_ms)
            self.enqueue(delivery.id)
        await db.commit()


class MockReceiver:
    def __init__(self) -> None:
        self.deliveries: list[dict[str, Any]] = []

    async def __call__(self, request: httpx.Request) -> httpx.Response:
        body = request.read()
        self.deliveries.append(
            {
                "headers": dict(request.headers),
                "body": body.decode(),
            }
        )
        return httpx.Response(200, json={"ok": True})


webhook_queue = WebhookQueue()

ReceiverHandler = Callable[[httpx.Request], Awaitable[httpx.Response]]
