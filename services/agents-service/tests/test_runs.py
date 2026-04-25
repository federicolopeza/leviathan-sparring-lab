from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient

AuthHeaders = Callable[..., dict[str, str]]


async def test_create_list_get_and_cancel_run(
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    headers = auth_headers("user-a", "org-a")

    create_response = await client.post(
        "/v1/agents/runs",
        json={"name": "summarize", "input_json": {"prompt": "Hello {{ user }}"}},
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "summarize"
    assert created["status"] == "queued"
    assert created["user_id"] == "user-a"
    assert created["org_id"] == "org-a"
    assert created["input_json"] == {"prompt": "Hello {{ user }}"}

    list_response = await client.get("/v1/agents/runs", headers=headers)
    assert list_response.status_code == 200
    runs = list_response.json()
    assert len(runs) == 1
    assert runs[0]["id"] == created["id"]

    get_response = await client.get(f"/v1/agents/runs/{created['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]

    cancel_response = await client.post(
        f"/v1/agents/runs/{created['id']}/cancel",
        headers=headers,
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"


async def test_list_runs_only_current_user(
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    await client.post(
        "/v1/agents/runs",
        json={"name": "a", "input_json": {"prompt": "A"}},
        headers=auth_headers("user-a"),
    )
    await client.post(
        "/v1/agents/runs",
        json={"name": "b", "input_json": {"prompt": "B"}},
        headers=auth_headers("user-b"),
    )

    response = await client.get("/v1/agents/runs", headers=auth_headers("user-a"))

    assert response.status_code == 200
    runs = response.json()
    assert len(runs) == 1
    assert runs[0]["user_id"] == "user-a"
