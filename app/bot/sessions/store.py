from dataclasses import dataclass


@dataclass
class UserSession:
    access_token: str
    refresh_token: str
    email: str


class SessionStore:
    """In-memory auth sessions keyed by Telegram user id."""

    def __init__(self) -> None:
        self._sessions: dict[int, UserSession] = {}

    def get(self, telegram_user_id: int) -> UserSession | None:
        return self._sessions.get(telegram_user_id)

    def set(self, telegram_user_id: int, session: UserSession) -> None:
        self._sessions[telegram_user_id] = session

    def clear(self, telegram_user_id: int) -> None:
        self._sessions.pop(telegram_user_id, None)

    def update_tokens(
        self,
        telegram_user_id: int,
        *,
        access_token: str,
        refresh_token: str,
    ) -> None:
        session = self._sessions.get(telegram_user_id)
        if session is None:
            return
        session.access_token = access_token
        session.refresh_token = refresh_token
