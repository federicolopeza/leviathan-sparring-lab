from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient


async def test_list_users_admin_only_succeeds(
    client: AsyncClient,
    auth_headers: Callable[[str, bool], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    response = await client.get(
        "/v1/admin/users",
        headers=auth_headers(user_ids["admin"], True),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2


async def test_list_users_non_admin_403(
    client: AsyncClient,
    auth_headers: Callable[[str, bool], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    response = await client.get(
        "/v1/admin/users",
        headers=auth_headers(user_ids["regular"], False),
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not Found"}


async def test_get_user_detail_returns_unescaped_bio(
    client: AsyncClient,
    auth_headers: Callable[[str, bool], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    response = await client.get(
        f"/v1/admin/users/{user_ids['admin']}",
        headers=auth_headers(user_ids["admin"], True),
    )

    assert response.status_code == 200
    assert response.json()["bio"] == "<script>alert(1)</script>"


async def test_v_t3_007_api_key_scope_startswith_bypass(
    client: AsyncClient,
    auth_headers: Callable[[str, bool], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    response = await client.post(
        "/v1/admin/api-keys",
        json={"name": "bypass", "scopes": ["read.admin"]},
        headers=auth_headers(user_ids["admin"], True),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["scopes"] == ["read.admin"]
    assert body["key"]


async def test_v_t4_009_ssti_jinja2_dump(
    client: AsyncClient,
    auth_headers: Callable[[str, bool], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    response = await client.post(
        "/v1/admin/branding",
        json={"welcome_message": "{{ ''.__class__.__mro__[1].__subclasses__() }}"},
        headers=auth_headers(user_ids["admin"], True),
    )

    assert response.status_code == 200
    assert "<class" in response.json()["rendered_html"]


async def test_v_t3_004_xforwarded_user_with_cluster_internal_bypasses_jwt(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/v1/admin/internal-action",
        json={"action": "dump_audit"},
        headers={
            "X-Forwarded-User": "spoofed-admin",
            "X-Cluster-Internal": "1",
        },
    )

    assert response.status_code == 200
    assert response.json()["actor_user_id"] == "spoofed-admin"


async def test_v_t3_004_xforwarded_user_without_cluster_header_rejected(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/v1/admin/internal-action",
        json={"action": "dump_audit"},
        headers={"X-Forwarded-User": "spoofed-admin"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not Found"}


async def test_health_ready_leaks_build(client: AsyncClient) -> None:
    response = await client.get("/v1/health/ready")

    assert response.status_code == 200
    assert response.json()["build_hash"] == "test-build"
    assert response.json()["git_sha"] == "test-sha"
    assert response.json()["service_version"] == "test-version"
