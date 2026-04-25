from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient

AuthHeaders = Callable[..., dict[str, str]]


async def test_v_t5_001_second_user_can_read_first_users_run(
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    create_response = await client.post(
        "/v1/agents/runs",
        json={"name": "private-analysis", "input_json": {"prompt": "secret"}},
        headers=auth_headers("user-a"),
    )
    assert create_response.status_code == 201
    run_id = create_response.json()["id"]

    response = await client.get(f"/v1/agents/runs/{run_id}", headers=auth_headers("user-b"))

    assert response.status_code == 200
    assert response.json()["user_id"] == "user-a"
