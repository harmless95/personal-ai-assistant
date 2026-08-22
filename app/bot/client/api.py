from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from app.bot.client.errors import ApiClientError


class AssistantApiClient:
    def __init__(self, *, base_url: str, api_prefix: str = "/api/v1") -> None:
        self._api_prefix = api_prefix.rstrip("/")
        self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=30.0)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def login(self, *, email: str, password: str) -> dict[str, Any]:
        response = await self._client.post(
            f"{self._api_prefix}/auth/login",
            data={"username": email, "password": password},
        )
        return self._parse(response)

    async def refresh(self, *, refresh_token: str) -> dict[str, Any]:
        response = await self._client.post(
            f"{self._api_prefix}/auth/token/refresh",
            json={"refresh_token": refresh_token},
        )
        return self._parse(response)

    async def ask_checkin(self, *, access_token: str, state: dict[str, int]) -> dict[str, Any]:
        response = await self._client.post(
            f"{self._api_prefix}/daily/checkin/ask/",
            headers=self._bearer(access_token),
            json={"state": state},
        )
        return self._parse(response)

    async def answer_checkin(
        self,
        *,
        access_token: str,
        checkin_id: UUID | str,
        answers: list[dict[str, str]],
    ) -> dict[str, Any]:
        response = await self._client.post(
            f"{self._api_prefix}/daily/checkin/answer/",
            headers=self._bearer(access_token),
            json={"checkin_id": str(checkin_id), "answers": answers},
        )
        return self._parse(response)

    async def get_artifact(self, *, access_token: str, checkin_id: UUID | str) -> dict[str, Any]:
        response = await self._client.get(
            f"{self._api_prefix}/daily/checkin/{checkin_id}/artifact/",
            headers=self._bearer(access_token),
        )
        return self._parse(response)

    async def get_history(
        self,
        *,
        access_token: str,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        response = await self._client.get(
            f"{self._api_prefix}/daily/checkin/history/",
            headers=self._bearer(access_token),
            params={"limit": limit, "offset": offset},
        )
        return self._parse(response)

    @staticmethod
    def _bearer(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}

    @staticmethod
    def _parse(response: httpx.Response) -> dict[str, Any]:
        if response.is_success:
            payload = response.json()
            if isinstance(payload, dict):
                return payload
            raise ApiClientError("Unexpected API response shape", status_code=response.status_code)

        raise ApiClientError(_extract_detail(response), status_code=response.status_code)


def _extract_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or f"HTTP {response.status_code}"

    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, dict):
            message = detail.get("message") or detail.get("code")
            if message:
                return str(message)
        if isinstance(detail, str):
            return detail
        if "message" in payload:
            return str(payload["message"])
    return f"HTTP {response.status_code}"
