from __future__ import annotations

from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.client import ApiClientError, AssistantApiClient
from app.bot.services import AuthRequiredError, call_with_refresh
from app.bot.sessions import SessionStore
from app.bot.ui import format_history

router = Router(name="checkin_history")


@router.message(Command("history"))
async def cmd_history(
    message: Message,
    api: AssistantApiClient,
    sessions: SessionStore,
) -> None:
    if message.from_user is None:
        return
    try:

        async def _history(access_token: str) -> dict[str, Any]:
            return await api.get_history(access_token=access_token, limit=10, offset=0)

        payload = await call_with_refresh(
            api=api,
            store=sessions,
            telegram_user_id=message.from_user.id,
            action=_history,
        )
    except AuthRequiredError:
        await message.answer("Сначала войди: /login")
        return
    except ApiClientError as error:
        await message.answer(f"Не удалось загрузить историю: {error}")
        return

    items = payload.get("items") or []
    await message.answer(format_history(items if isinstance(items, list) else []))
