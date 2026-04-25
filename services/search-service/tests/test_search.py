from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient


async def test_search_returns_matching_documents(
    client: AsyncClient,
    auth_headers: Callable[[str, str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    response = await client.get(
        "/v1/search",
        params={"q": "payments"},
        headers=auth_headers(user_ids["a"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert {result["title"] for result in payload["results"]} == {
        "Uruguay fintech payments",
        "Argentina payments ledger",
    }


async def test_search_no_match_returns_empty(
    client: AsyncClient,
    auth_headers: Callable[[str, str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    response = await client.get(
        "/v1/search",
        params={"q": "does-not-exist"},
        headers=auth_headers(user_ids["a"]),
    )

    assert response.status_code == 200
    assert response.json()["results"] == []


async def test_search_pagination(
    client: AsyncClient,
    auth_headers: Callable[[str, str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    first = await client.get(
        "/v1/search",
        params={"q": "fintech", "page": 1, "per_page": 1},
        headers=auth_headers(user_ids["a"]),
    )
    second = await client.get(
        "/v1/search",
        params={"q": "fintech", "page": 2, "per_page": 1},
        headers=auth_headers(user_ids["a"]),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["per_page"] == 1
    assert first.json()["total"] == 2
    assert first.json()["results"][0]["id"] != second.json()["results"][0]["id"]


async def test_saved_search_create_and_list(
    client: AsyncClient,
    auth_headers: Callable[[str, str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    headers = auth_headers(user_ids["a"])
    create = await client.post(
        "/v1/search/saved",
        json={"name": "Payments", "query": "payments"},
        headers=headers,
    )
    listing = await client.get("/v1/search/saved", headers=headers)

    assert create.status_code == 201
    assert listing.status_code == 200
    assert listing.json()[0]["id"] == create.json()["saved_search_id"]
    assert listing.json()[0]["query"] == "payments"


async def test_saved_search_run_returns_results(
    client: AsyncClient,
    auth_headers: Callable[[str, str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    headers = auth_headers(user_ids["a"])
    create = await client.post(
        "/v1/search/saved",
        json={"name": "Credit", "query": "credit"},
        headers=headers,
    )
    response = await client.post(
        f"/v1/search/saved/{create.json()['saved_search_id']}/run",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["title"] == "Chile credit scoring"


async def test_saved_search_run_only_own(
    client: AsyncClient,
    auth_headers: Callable[[str, str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    create = await client.post(
        "/v1/search/saved",
        json={"name": "Payments", "query": "payments"},
        headers=auth_headers(user_ids["a"]),
    )
    response = await client.post(
        f"/v1/search/saved/{create.json()['saved_search_id']}/run",
        headers=auth_headers(user_ids["b"]),
    )

    assert response.status_code == 404


async def test_v_t4_008_sqli_via_saved_search_run(
    client: AsyncClient,
    auth_headers: Callable[[str, str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    # Comment-truncate trailing %' so UNION returns rows from ALL orgs (incl. ORG_B).
    payload = (
        "x%' UNION SELECT id,org_id,title,body,tags,created_at,updated_at "
        "FROM indexed_documents -- "
    )
    headers = auth_headers(user_ids["a"])
    create = await client.post(
        "/v1/search/saved",
        json={"name": "Injected", "query": payload},
        headers=headers,
    )
    response = await client.post(
        f"/v1/search/saved/{create.json()['saved_search_id']}/run",
        headers=headers,
    )

    assert response.status_code == 200
    assert any(
        result["org_id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        for result in response.json()["results"]
    )


async def test_v_t4_008_parameterized_search_is_safe(
    client: AsyncClient,
    auth_headers: Callable[[str, str], dict[str, str]],
    user_ids: dict[str, str],
) -> None:
    # Same comment-truncate payload as the SQLi reproducer — but parameterized path
    # binds it as a single LIKE term; UNION never executes.
    payload = (
        "x%' UNION SELECT id,org_id,title,body,tags,created_at,updated_at "
        "FROM indexed_documents -- "
    )
    response = await client.get(
        "/v1/search",
        params={"q": payload},
        headers=auth_headers(user_ids["a"]),
    )

    assert response.status_code == 200
    assert response.json()["results"] == []


async def test_health_ready_leaks_build(client: AsyncClient) -> None:
    response = await client.get("/v1/health/ready")

    assert response.status_code == 200
    assert response.json()["build_hash"] == "test-build"
