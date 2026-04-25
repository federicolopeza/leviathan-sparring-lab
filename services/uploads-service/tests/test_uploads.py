from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import respx
from app.config import get_settings
from app.database import SessionLocal
from app.models import Upload
from httpx import AsyncClient, Response
from sqlalchemy import select


async def _post_upload(
    client: AsyncClient,
    headers: dict[str, str],
    content: bytes,
    filename: str = "avatar.jpg",
    purpose: str = "avatar",
) -> Response:
    return await client.post(
        "/v1/uploads",
        data={"purpose": purpose},
        files={"file": (filename, content, "application/octet-stream")},
        headers=headers,
    )


async def test_upload_jpeg_succeeds(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    response = await _post_upload(client, auth_headers(user_ids["a"]), b"\xff\xd8\xffjpeg")

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "avatar.jpg"
    async with SessionLocal() as db:
        result = await db.execute(select(Upload).where(Upload.id == body["upload_id"]))
        upload = result.scalar_one()
    assert upload.mime_type == "image/jpeg"
    assert upload.size_bytes == 7


async def test_upload_polyglot_php_after_jpeg_accepts(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    response = await _post_upload(
        client,
        auth_headers(user_ids["a"]),
        b"\xff\xd8\xffEXIF<?php echo 1; ?>",
        filename="polyglot.php.jpg",
    )

    assert response.status_code == 201


async def test_upload_text_rejected(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    response = await _post_upload(client, auth_headers(user_ids["a"]), b"hello world")

    assert response.status_code == 422


async def test_upload_size_cap_enforced(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    response = await _post_upload(client, auth_headers(user_ids["a"]), b"\xff\xd8\xff" + b"a" * 65)

    assert response.status_code == 413


async def test_get_upload_normal_returns_file(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    headers = auth_headers(user_ids["a"])
    await _post_upload(client, headers, b"\xff\xd8\xffjpeg", filename="normal.jpg")

    async with SessionLocal() as db:
        result = await db.execute(select(Upload).where(Upload.original_filename == "normal.jpg"))
        upload = result.scalar_one()

    response = await client.get(f"/v1/uploads/{upload.storage_key}", headers=headers)

    assert response.status_code == 200
    assert response.content == b"\xff\xd8\xffjpeg"


async def test_get_upload_path_traversal_reads_outside_dir(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    settings = get_settings()
    cache_dir = Path(settings.MINIO_LOCAL_CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)  # noqa: ASYNC240
    secret = cache_dir.parent / "secret.txt"
    secret.write_bytes(b"outside-secret")  # noqa: ASYNC240

    response = await client.get("/v1/uploads/..%2Fsecret.txt", headers=auth_headers(user_ids["a"]))

    assert response.status_code == 200
    assert response.content == b"outside-secret"


async def test_list_uploads_only_own(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    await _post_upload(client, auth_headers(user_ids["a"]), b"\xff\xd8\xffa", filename="a.jpg")
    await _post_upload(client, auth_headers(user_ids["b"]), b"\xff\xd8\xffb", filename="b.jpg")

    response = await client.get("/v1/uploads", headers=auth_headers(user_ids["a"]))

    assert response.status_code == 200
    assert [item["filename"] for item in response.json()] == ["a.jpg"]


async def test_delete_upload_only_own(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    create_response = await _post_upload(
        client,
        auth_headers(user_ids["b"]),
        b"\xff\xd8\xffb",
        filename="b.jpg",
    )
    upload_id = create_response.json()["upload_id"]

    response = await client.delete(f"/v1/uploads/{upload_id}", headers=auth_headers(user_ids["a"]))

    assert response.status_code in {403, 404}


@respx.mock
async def test_avatar_fetch_169_254_metadata(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    respx.get("http://169.254.169.254/latest/meta-data/").mock(
        return_value=Response(200, content=b"instance-id")
    )

    response = await client.post(
        "/v1/uploads/avatar-fetch",
        json={"image_url": "http://169.254.169.254/latest/meta-data/"},
        headers=auth_headers(user_ids["a"]),
    )

    assert response.status_code == 201
    assert response.json()["sha256"]


@respx.mock
async def test_avatar_fetch_external_url_succeeds(
    client: AsyncClient,
    auth_headers: Callable[[str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    respx.get("https://example.com/avatar.png").mock(
        return_value=Response(200, content=bytes.fromhex("89504E47") + b"png")
    )

    response = await client.post(
        "/v1/uploads/avatar-fetch",
        json={"image_url": "https://example.com/avatar.png"},
        headers=auth_headers(user_ids["a"]),
    )

    assert response.status_code == 201


async def test_health_ready_leaks_build(client: AsyncClient) -> None:
    response = await client.get("/v1/health/ready")

    assert response.status_code == 200
    assert response.json()["build_hash"] == "test-build"
