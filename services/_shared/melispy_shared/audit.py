"""Tamper-evident audit log helpers."""

from __future__ import annotations

import hashlib
import hmac as hmaclib
import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from melispy_shared.models import AuditLog


class AuditEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ts: datetime
    event_type: str
    actor_id: str
    resource: str
    action: str
    payload: dict[str, object] = Field(default_factory=dict)
    prev_hash: str
    hmac: str


async def emit_audit(
    session: AsyncSession,
    event_type: str,
    actor_id: str,
    resource: str,
    action: str,
    payload: dict[str, object],
) -> AuditLog:
    prev_hash = await _last_hmac(session)
    entry = AuditEntry(
        ts=datetime.now(UTC),
        event_type=event_type,
        actor_id=actor_id,
        resource=resource,
        action=action,
        payload=payload,
        prev_hash=prev_hash,
        hmac="",
    )
    digest = _compute_hmac(prev_hash, entry)
    row = AuditLog(
        tenant_id=_tenant_from_payload(payload),
        ts=entry.ts,
        event_type=event_type,
        actor_id=actor_id,
        resource=resource,
        action=action,
        payload=payload,
        prev_hash=prev_hash,
        hmac=digest,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def verify_chain(session: AsyncSession) -> bool:
    result = await session.execute(select(AuditLog).order_by(AuditLog.ts.asc(), AuditLog.id.asc()))
    previous = ""
    for row in result.scalars():
        entry = AuditEntry(
            ts=row.ts,
            event_type=row.event_type,
            actor_id=row.actor_id,
            resource=row.resource,
            action=row.action,
            payload=row.payload,
            prev_hash=row.prev_hash,
            hmac="",
        )
        if row.prev_hash != previous:
            return False
        expected = _compute_hmac(previous, entry)
        if not hmaclib.compare_digest(expected, row.hmac):
            return False
        previous = row.hmac
    return True


async def _last_hmac(session: AsyncSession) -> str:
    result = await session.execute(
        select(AuditLog.hmac)
        .order_by(AuditLog.ts.desc(), AuditLog.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none() or ""


def _compute_hmac(prev_hash: str, entry: AuditEntry) -> str:
    key = os.getenv("AUDIT_LOG_HMAC_KEY", "dev-audit-key").encode()
    message = (
        prev_hash
        + entry.event_type
        + entry.actor_id
        + entry.resource
        + entry.action
    ).encode()
    return hmaclib.new(key, message, hashlib.sha256).hexdigest()


def _canonical_ts(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _tenant_from_payload(payload: dict[str, object]) -> UUID:
    value = payload.get("tenant_id")
    if isinstance(value, str):
        return UUID(value)
    if isinstance(value, UUID):
        return value
    return uuid4()
