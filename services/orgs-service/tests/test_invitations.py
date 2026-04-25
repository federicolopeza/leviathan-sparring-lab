from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta

from app.crud.invitations import create_invitation, hash_token
from app.deps.db import SessionLocal
from app.models import OrgRole
from app.models.base import now_utc
from httpx import AsyncClient


async def test_create_invitation_returns_id_only_no_raw_token(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    create_org: Callable[[str | None], object],
    user_ids: dict[str, str],
    monkeypatch: object,
) -> None:
    org = await create_org()
    monkeypatch.setattr("app.routes.invitations.secrets.token_hex", lambda _size: "raw-token")

    response = await client.post(
        f"/v1/orgs/{org['id']}/invitations",
        json={"email": "invitee@example.com", "role": "member"},
        headers=auth_headers(user_ids["owner"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"invitation_id", "expires_at"}
    assert "token" not in body
    assert "raw-token" not in response.text


async def test_accept_invitation_creates_membership(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    create_org: Callable[[str | None], object],
    user_ids: dict[str, str],
    monkeypatch: object,
) -> None:
    org = await create_org()
    monkeypatch.setattr("app.routes.invitations.secrets.token_hex", lambda _size: "join-token")
    await client.post(
        f"/v1/orgs/{org['id']}/invitations",
        json={"email": "invitee@example.com", "role": "member"},
        headers=auth_headers(user_ids["owner"]),
    )

    response = await client.post(
        "/v1/orgs/invitations/accept",
        json={"token": "join-token"},
        headers=auth_headers(user_ids["invitee"]),
    )

    assert response.status_code == 200
    assert response.json()["org_id"] == org["id"]
    assert response.json()["user_id"] == user_ids["invitee"]


async def test_accept_invitation_used_once_replay_rejected(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    create_org: Callable[[str | None], object],
    user_ids: dict[str, str],
    monkeypatch: object,
) -> None:
    org = await create_org()
    monkeypatch.setattr("app.routes.invitations.secrets.token_hex", lambda _size: "once-token")
    await client.post(
        f"/v1/orgs/{org['id']}/invitations",
        json={"email": "invitee@example.com", "role": "member"},
        headers=auth_headers(user_ids["owner"]),
    )
    first = await client.post(
        "/v1/orgs/invitations/accept",
        json={"token": "once-token"},
        headers=auth_headers(user_ids["invitee"]),
    )
    assert first.status_code == 200

    replay = await client.post(
        "/v1/orgs/invitations/accept",
        json={"token": "once-token"},
        headers=auth_headers(user_ids["outsider"]),
    )

    assert replay.status_code == 400


async def test_accept_invitation_expired_rejected(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    create_org: Callable[[str | None], object],
    user_ids: dict[str, str],
) -> None:
    org = await create_org()
    async with SessionLocal() as db:
        await create_invitation(
            db,
            org_id=str(org["id"]),
            email="expired@example.com",
            role=OrgRole.MEMBER,
            token_hash=hash_token("expired-token"),
            expires_at=now_utc() - timedelta(days=1),
        )
        await db.commit()

    response = await client.post(
        "/v1/orgs/invitations/accept",
        json={"token": "expired-token"},
        headers=auth_headers(user_ids["invitee"]),
    )

    assert response.status_code == 400
