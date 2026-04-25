from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient

AuthHeaders = Callable[..., dict[str, str]]


async def test_v_t6_001_render_endpoint_executes_jinja_expression(
    client: AsyncClient,
    auth_headers: AuthHeaders,
) -> None:
    headers = auth_headers("user-a")
    create_response = await client.post(
        "/v1/agents/runs",
        json={"name": "render", "input_json": {"prompt": "{{7*7}}"}},
        headers=headers,
    )
    assert create_response.status_code == 201
    run_id = create_response.json()["id"]

    response = await client.post(f"/v1/agents/runs/{run_id}/render", headers=headers)

    assert response.status_code == 200
    assert "49" in response.text
