from __future__ import annotations

from httpx import AsyncClient


async def test_v_t8_001_imds_v1_unauthenticated_no_token_required(
    client: AsyncClient,
) -> None:
    response = await client.get("/latest/meta-data/iam/security-credentials/melispy-app")

    # V-T8-001 REPRODUCER: IMDSv1 unauthenticated access confirmed
    assert response.status_code == 200
    assert response.json()["Code"] == "Success"


async def test_imdsv2_token_endpoint_returns_token(client: AsyncClient) -> None:
    response = await client.get("/latest/api/token")

    assert response.status_code == 200
    assert response.text
