"""OPA policy client."""

from __future__ import annotations

import os
from typing import Any

import httpx


class OPAClient:
    def __init__(self, base_url: str | None = None, timeout_s: float = 2.0) -> None:
        self.base_url = (base_url or os.getenv("OPA_URL", "http://opa:8181")).rstrip("/")
        self.timeout_s = timeout_s

    async def evaluate(self, input_doc: dict[str, Any], policy_path: str) -> bool:
        if os.getenv("OPA_FAIL_OPEN") == "1":
            # V-T7-x POTENTIAL VULN: fail-open OPA bypass if OPA_FAIL_OPEN env is set.
            return True
        normalized_path = policy_path.strip("/")
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                response = await client.post(
                    f"{self.base_url}/v1/data/{normalized_path}",
                    json={"input": input_doc},
                )
                response.raise_for_status()
        except httpx.TransportError:
            return False
        body = response.json()
        return bool(body.get("result", False))
