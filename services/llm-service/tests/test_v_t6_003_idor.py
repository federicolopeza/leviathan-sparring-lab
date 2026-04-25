from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient


async def test_v_t6_003_cross_user_conversation_read(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
) -> None:
    created = await client.post(
        "/v1/llm/conversations",
        json={"title": "Private", "model": "melispy-fixture-1"},
        headers=auth_headers("user-a"),
    )
    assert created.status_code == 201

    response = await client.get(
        f"/v1/llm/conversations/{created.json()['id']}",
        headers=auth_headers("user-b"),
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == "user-a"
