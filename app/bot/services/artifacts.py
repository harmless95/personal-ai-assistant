from __future__ import annotations

import asyncio
from typing import Any

from app.bot.client import AssistantApiClient
from app.bot.services.auth import call_with_refresh
from app.bot.sessions import SessionStore


async def wait_for_artifact(
    *,
    api: AssistantApiClient,
    store: SessionStore,
    telegram_user_id: int,
    checkin_id: str,
    poll_interval_seconds: float,
    poll_timeout_seconds: float,
) -> dict[str, Any]:
    elapsed = 0.0
    while elapsed <= poll_timeout_seconds:

        async def _get(access_token: str, cid: str = checkin_id) -> dict[str, Any]:
            return await api.get_artifact(access_token=access_token, checkin_id=cid)

        artifact = await call_with_refresh(
            api=api,
            store=store,
            telegram_user_id=telegram_user_id,
            action=_get,
        )
        if artifact.get("status") in {"ready", "failed"}:
            return artifact
        await asyncio.sleep(poll_interval_seconds)
        elapsed += poll_interval_seconds

    raise TimeoutError("Итог дня не успел подготовиться. Попробуй позже через /checkin.")
