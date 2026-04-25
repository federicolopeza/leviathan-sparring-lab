from __future__ import annotations

import re

from httpx import AsyncClient


async def test_meta_data_index_returns_keys(client: AsyncClient) -> None:
    response = await client.get("/latest/meta-data/")

    assert response.status_code == 200
    assert "instance-id" in response.text
    assert "iam/" in response.text


async def test_instance_id_constant(client: AsyncClient) -> None:
    response = await client.get("/latest/meta-data/instance-id")

    assert response.status_code == 200
    assert response.text == "i-0melispy12345678"


async def test_iam_credentials_format_valid(client: AsyncClient) -> None:
    response = await client.get("/latest/meta-data/iam/security-credentials/melispy-app")

    assert response.status_code == 200
    payload = response.json()
    assert re.match(r"^ASIA[A-Z0-9]{16}$", payload["AccessKeyId"])
    assert len(payload["SecretAccessKey"]) >= 30
    assert len(payload["Token"]) >= 100


async def test_iam_credentials_stable_across_requests(client: AsyncClient) -> None:
    first = await client.get("/latest/meta-data/iam/security-credentials/melispy-app")
    second = await client.get("/latest/meta-data/iam/security-credentials/melispy-app")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["AccessKeyId"] == second.json()["AccessKeyId"]


async def test_dynamic_identity_document_shape(client: AsyncClient) -> None:
    response = await client.get("/latest/dynamic/instance-identity/document")

    assert response.status_code == 200
    payload = response.json()
    for key in ("accountId", "instanceId", "region", "instanceType"):
        assert key in payload
