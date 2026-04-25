from __future__ import annotations

from uuid import uuid4

from melispy_shared.audit import emit_audit, verify_chain
from melispy_shared.models import AuditLog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def test_chain_integrity(async_session: AsyncSession) -> None:
    tenant_id = str(uuid4())
    await emit_audit(
        async_session,
        "auth.login",
        "user-1",
        "session",
        "create",
        {"tenant_id": tenant_id, "ip": "10.0.0.1"},
    )
    await emit_audit(
        async_session,
        "billing.checkout",
        "user-1",
        "invoice",
        "create",
        {"tenant_id": tenant_id, "amount": 100},
    )

    assert await verify_chain(async_session) is True


async def test_chain_tamper_detected(async_session: AsyncSession) -> None:
    tenant_id = str(uuid4())
    await emit_audit(
        async_session,
        "auth.login",
        "user-1",
        "session",
        "create",
        {"tenant_id": tenant_id, "ip": "10.0.0.1"},
    )
    await emit_audit(
        async_session,
        "billing.checkout",
        "user-1",
        "invoice",
        "create",
        {"tenant_id": tenant_id, "amount": 100},
    )
    result = await async_session.execute(
        select(AuditLog).where(AuditLog.action == "create").limit(1)
    )
    row = result.scalar_one()
    row.payload = {**row.payload, "ip": "203.0.113.10"}
    await async_session.commit()

    assert await verify_chain(async_session) is False
