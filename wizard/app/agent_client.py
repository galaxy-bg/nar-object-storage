"""Client helpers for talking to kdx-agent."""

import os
from typing import Any

import httpx

AGENT_URL = os.environ.get("KDX_AGENT_URL", "http://127.0.0.1:7070")
TIMEOUT_SECONDS = 3.0


class AgentUnavailable(RuntimeError):
    pass


class AgentClient:
    def __init__(self, base_url: str = AGENT_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def verify_challenge(self, challenge_key: str) -> bool:
        data = self._request("POST", "/challenge/verify", json={"challenge_key": challenge_key})
        return bool(data.get("valid"))

    def network_interfaces(self) -> list[dict[str, Any]]:
        data = self._request("GET", "/discover/network")
        return data.get("interfaces", [])

    def disks(self) -> list[dict[str, Any]]:
        data = self._request("GET", "/discover/disks")
        return data.get("disks", [])

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
                response = client.request(method, f"{self.base_url}{path}", **kwargs)
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AgentUnavailable(str(exc)) from exc
