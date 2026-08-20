from collections.abc import Awaitable
from typing import NoReturn, TypeVar

from app.api.daily_checkin.data.daily_checkin_repository import DailyCheckinRepository
from app.api.daily_checkin.data.errors import (
    DatabaseError,
    DatabaseUnavailableError,
    DuplicateEntryError,
    ForeignKeyViolationError,
    IntegrityViolationError,
    NotNullViolationError,
)
from app.api.daily_checkin.errors import DailyCheckinErrors, raise_error
from app.api.daily_checkin.models.daily import (
    AnswerCheckinRequest,
    AnswerCheckinResponse,
    AskCheckinRequest,
    AskCheckinResponse,
    CheckinStatus,
)
from app.api.daily_checkin.utils.check_tag import state_to_tags
from app.api.daily_checkin.utils.checkin import (
    answers_match_questions,
    attach_answers_and_artifact,
    build_asked_checkin,
)
from app.api.daily_checkin.utils.questions import (
    blocked_by_cooldown,
    select_questions,
    to_question_pool_item,
    to_selected_question,
)
from app.api.daily_checkin.utils.summary import (
    build_answer_response,
    map_answers_by_category,
    structured_summary_from_response,
)
from app.db import DailyCheckin

T = TypeVar("T")

_DB_ERRORS = (
    ForeignKeyViolationError,
    NotNullViolationError,
    IntegrityViolationError,
    DatabaseUnavailableError,
    DatabaseError,
)


class DailyCheckinService:
    def __init__(self, repository: DailyCheckinRepository):
        self.repository = repository

    async def question_handler(self, client_data: AskCheckinRequest) -> AskCheckinResponse:
        existing = await self._db(
            self.repository.get_today_checkin(
                user_id=client_data.user_id,
                with_questions=True,
            )
        )
        if existing is not None:
            if existing.status == CheckinStatus.ANSWERED:
                raise_error(DailyCheckinErrors.CHECKIN_ALREADY_EXISTS)
            return self._ask_response_from_checkin(existing)

        tags = state_to_tags(state=client_data.state)
        pool_rows = await self._db(self.repository.list_active_questions())
        pool = [to_question_pool_item(row) for row in pool_rows]

        max_cooldown = max((question.cooldown_days for question in pool), default=0)
        usage, today = await self._db(
            self.repository.list_recent_question_usage(
                user_id=client_data.user_id,
                max_cooldown_days=max_cooldown,
            )
        )
        cooldown_blocked = blocked_by_cooldown(pool, usage, today=today)

        selected = select_questions(pool=pool, tags=tags, cooldown_blocked=cooldown_blocked)
        if selected is None:
            raise_error(DailyCheckinErrors.QUESTION_POOL_EMPTY)

        checkin = build_asked_checkin(
            user_id=client_data.user_id,
            state=client_data.state,
            questions=selected,
        )
        checkin = await self._db(
            self.repository.create_checkin(checkin=checkin),
            on_duplicate=DailyCheckinErrors.CHECKIN_ALREADY_EXISTS,
        )

        return AskCheckinResponse(
            checkin_id=checkin.id,
            date=checkin.checkin_date,
            selected_questions=selected,
        )

    async def answer_handler(self, question_data: AnswerCheckinRequest) -> AnswerCheckinResponse:
        checkin = await self._db(
            self.repository.get_checkin_by_id(
                checkin_id=question_data.checkin_id,
                with_questions=True,
                with_answers=True,
                with_artifact=True,
            )
        )
        if checkin is None:
            raise_error(DailyCheckinErrors.CHECKIN_NOT_FOUND)
        if checkin.user_id != question_data.user_id:
            raise_error(DailyCheckinErrors.CHECKIN_FORBIDDEN)
        if checkin.status == CheckinStatus.ANSWERED:
            raise_error(DailyCheckinErrors.CHECKIN_ALREADY_ANSWERED)
        if not answers_match_questions(checkin.questions, question_data.answers):
            raise_error(DailyCheckinErrors.INVALID_ANSWERS)

        answers_by_category = map_answers_by_category(
            questions=checkin.questions,
            answers=question_data.answers,
        )
        response = build_answer_response(
            checkin_id=question_data.checkin_id,
            answers_by_category=answers_by_category,
        )

        attach_answers_and_artifact(
            checkin,
            answers=question_data.answers,
            structured_summary=structured_summary_from_response(response),
        )
        await self._db(self.repository.save_checkin(checkin=checkin))
        return response

    def _ask_response_from_checkin(self, checkin: DailyCheckin) -> AskCheckinResponse:
        selected = sorted(
            (to_selected_question(question) for question in checkin.questions),
            key=lambda question: question.order,
        )
        return AskCheckinResponse(
            checkin_id=checkin.id,
            date=checkin.checkin_date,
            selected_questions=selected,
        )

    async def _db(
        self,
        awaitable: Awaitable[T],
        *,
        on_duplicate: tuple[str, str, int] | None = None,
    ) -> T:
        try:
            return await awaitable
        except DuplicateEntryError as error:
            if on_duplicate is not None:
                raise_error(on_duplicate)
            self._map_db_error_to_http(error)
        except _DB_ERRORS as error:
            self._map_db_error_to_http(error)

    def _map_db_error_to_http(self, error: Exception) -> NoReturn:
        if isinstance(error, DatabaseUnavailableError):
            raise_error(DailyCheckinErrors.DATABASE_UNAVAILABLE)
        raise_error(DailyCheckinErrors.DATABASE_ERROR)
