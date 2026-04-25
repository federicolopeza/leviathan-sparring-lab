from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient


async def test_create_list_get_conversation_and_add_message(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
) -> None:
    headers = auth_headers("user-a")

    created = await client.post(
        "/v1/llm/conversations",
        json={"title": "First thread", "model": "melispy-fixture-1"},
        headers=headers,
    )
    assert created.status_code == 201
    conversation = created.json()

    listed = await client.get("/v1/llm/conversations", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [conversation["id"]]

    fetched = await client.get(f"/v1/llm/conversations/{conversation['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["messages"] == []

    message = await client.post(
        f"/v1/llm/conversations/{conversation['id']}/messages",
        json={"role": "user", "content": "hello"},
        headers=headers,
    )
    assert message.status_code == 200
    body = message.json()
    assert body["user_message"]["content"] == "hello"
    assert body["assistant_message"]["role"] == "assistant"
    assert "MELISPY-ADMIN-2024" in body["assistant_message"]["content"]

    fetched_again = await client.get(f"/v1/llm/conversations/{conversation['id']}", headers=headers)
    assert len(fetched_again.json()["messages"]) == 2
