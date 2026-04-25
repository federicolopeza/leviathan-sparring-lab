from __future__ import annotations

from httpx import AsyncClient


async def test_avatar_stub_stores_url(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/v1/users/me/avatar",
        headers=auth_headers,
        json={"image_url": "https://cdn.melispy.com/avatars/ada.png"},
    )

    assert response.status_code == 200
    assert response.json() == {"avatar_url": "https://cdn.melispy.com/avatars/ada.png"}


async def test_avatar_rejects_non_image_extension(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/v1/users/me/avatar",
        headers=auth_headers,
        json={"image_url": "https://cdn.melispy.com/avatars/ada.svg"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request"}


async def test_avatar_rejects_http_only(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/v1/users/me/avatar",
        headers=auth_headers,
        json={"image_url": "http://cdn.melispy.com/avatars/ada.png"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request"}
