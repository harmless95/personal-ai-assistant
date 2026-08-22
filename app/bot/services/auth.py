from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.bot.client import ApiClientError, AssistantApiClient
from app.bot.sessions import SessionStore, UserSession

T = TypeVar("T")


class AuthRequiredError(Exception):
    pass


async def require_session(store: SessionStore, telegram_user_id: int) -> UserSession:
    session = store.get(telegram_user_id)
    if session is None:
        raise AuthRequiredError("Сначала войди: /login")
    return session


async def call_with_refresh(
    *,
    api: AssistantApiClient,
    store: SessionStore,
    telegram_user_id: int,
    action: Callable[[str], Awaitable[T]],
) -> T:
    session = await require_session(store, telegram_user_id)
    try:
        return await action(session.access_token)
    except ApiClientError as error:
        if error.status_code != 401:
            raise
        tokens = await api.refresh(refresh_token=session.refresh_token)
        store.update_tokens(
            telegram_user_id,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
        )
        return await action(tokens["access_token"])
