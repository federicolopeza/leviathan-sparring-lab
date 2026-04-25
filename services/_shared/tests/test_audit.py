from __future__ import annotations

from uuid import uuid4

from melispy_shared.audit import emit_audit, verify_chain
from melispy_shared.models import AuditLog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _write_three_entries(async_session: AsyncSession) -> None:
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
    await emit_audit(
        async_session,
        "asset.scan",
        "user-1",
        "target",
        "read",
        {"tenant_id": tenant_id, "target": "127.0.0.1"},
    )


async def test_verify_chain_valid(async_session: AsyncSession) -> None:
    await _write_three_entries(async_session)

    assert await verify_chain(async_session) is True


async def test_verify_chain_tampered(async_session: AsyncSession) -> None:
    await _write_three_entries(async_session)

    result = await async_session.execute(
        select(AuditLog).order_by(AuditLog.ts.asc(), AuditLog.id.asc()).offset(1).limit(1)
    )
    row = result.scalar_one()
    row.hmac = "0" * 64
    await async_session.commit()

    assert await verify_chain(async_session) is False
