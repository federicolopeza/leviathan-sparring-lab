from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from httpx import AsyncClient


async def test_email_dispatch_logs_to_stdout(
    client: AsyncClient,
    auth_headers: Callable[[str, bool, bool], dict[str, str]],
    capsys: Any,
) -> None:
    response = await client.post(
        "/v1/notifications/email",
        json={"to": "cliente@example.com", "template_id": "welcome", "vars": {"first_name": "Ana"}},
        headers=auth_headers(),
    )

    assert response.status_code == 200
    assert "cliente@example.com" in capsys.readouterr().out


async def test_template_list_includes_seeded(
    client: AsyncClient,
    auth_headers: Callable[[str, bool, bool], dict[str, str]],
) -> None:
    response = await client.get("/v1/notifications/templates", headers=auth_headers())

    assert response.status_code == 200
    assert {template["code"] for template in response.json()} == {
        "welcome",
        "invoice_issued",
        "password_reset",
        "magic_link",
        "member_invitation",
    }


async def test_v_t6_007_pdf_cmd_injection_in_invoice_number(
    client: AsyncClient,
    auth_headers: Callable[[str, bool, bool], dict[str, str]],
    monkeypatch: Any,
) -> None:
    commands: list[str] = []

    def fake_run(command: str, shell: bool, check: bool) -> object:
        commands.append(command)
        return object()

    monkeypatch.setattr("app.routes.notifications.subprocess.run", fake_run)
    payload = "; whoami #"
    response = await client.post(
        "/v1/notifications/invoice-pdf",
        json={"invoice_id": "inv-1", "invoice_number": payload},
        headers=auth_headers(),
    )

    assert response.status_code == 200
    assert payload in commands[0]


async def test_v_t6_006_imagemagick_svg_ephemeral_payload_unfiltered(
    client: AsyncClient,
    auth_headers: Callable[[str, bool, bool], dict[str, str]],
    monkeypatch: Any,
) -> None:
    commands: list[str] = []

    def fake_run(command: str, shell: bool, check: bool) -> object:
        commands.append(command)
        return object()

    monkeypatch.setattr("app.routes.notifications.subprocess.run", fake_run)
    svg_payload = "<svg><image href='ephemeral:|whoami'></image></svg>"
    Path(os.environ["MINIO_LOCAL_CACHE_DIR"], "avatar.svg").write_text(svg_payload)  # noqa: ASYNC240

    response = await client.post(
        "/v1/notifications/avatar-process",
        json={"upload_id": "avatar.svg"},
        headers=auth_headers(),
    )

    assert response.status_code == 200
    assert "ephemeral:|whoami" in commands[0]


def test_v_t7_005_minio_root_creds_in_env() -> None:
    assert os.environ["MINIO_ROOT_USER"] == "minioadmin"


async def test_dispatch_event_renders_email(
    client: AsyncClient,
    auth_headers: Callable[[str, bool, bool], dict[str, str]],
    capsys: Any,
) -> None:
    response = await client.post(
        "/v1/notifications/dispatch-event",
        json={
            "event_type": "invoice_issued",
            "target_user_id": "user-1",
            "payload": {
                "to": "facturacion@example.com",
                "vars": {"invoice_number": "F-100", "amount": "USD 10"},
            },
        },
        headers=auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["template_id"] == "invoice_issued"
    assert "facturacion@example.com" in capsys.readouterr().out


async def test_health_ready_leaks_build(client: AsyncClient) -> None:
    response = await client.get("/v1/health/ready")

    assert response.status_code == 200
    assert "build_hash" in response.json()
