from datetime import date
from typing import Any, cast
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.daily_checkin.models.daily import (
    AnswerCheckinRequest,
    AnswerItem,
    AskCheckinRequest,
    CheckinStatus,
    QuestionCategory,
    RequestState,
    SelectedQuestion,
)
from app.api.daily_checkin.services.service_daily import DailyCheckinService
from app.api.daily_checkin.tests.fixtures import (
    DEFAULT_POOL,
    Q_ACTION_01,
    Q_ACTION_02,
    Q_ENERGY_01,
    Q_FOCUS_02,
    Q_LEARNING_01,
    Q_RISK_01,
)
from app.api.daily_checkin.utils.questions import CATEGORIES
from app.db import DailyCheckin, DailyQuestion, QuestionPool


def _make_repository(
    *,
    create_return: DailyCheckin | None = None,
    get_return: DailyCheckin | None = None,
    existing_today: DailyCheckin | None = None,
    pool: list[QuestionPool] | None = None,
    usage: dict[Any, date] | None = None,
) -> Any:
    repository = Mock()
    repository.list_active_questions = AsyncMock(return_value=pool if pool is not None else DEFAULT_POOL)
    repository.list_recent_question_usage = AsyncMock(
        return_value=(usage if usage is not None else {}, date.today())
    )
    repository.get_today_checkin = AsyncMock(return_value=existing_today)
    repository.create_checkin = AsyncMock(return_value=create_return)
    repository.get_checkin_by_id = AsyncMock(return_value=get_return)
    repository.save_checkin = AsyncMock(return_value=get_return)
    return repository


def _asked_checkin(
    checkin_id: Any,
    questions: list[SelectedQuestion],
    *,
    user_id: Any | None = None,
) -> DailyCheckin:
    return DailyCheckin(
        id=checkin_id,
        user_id=user_id or uuid4(),
        checkin_date=date.today(),
        status=CheckinStatus.ASKED,
        stress_level=4,
        energy_level=2,
        plan_done=2,
        blocker_present=1,
        learning_done=3,
        questions=[
            DailyQuestion(
                question_id=question.question_id,
                category=question.category,
                text=question.text,
                sort_order=question.order,
            )
            for question in questions
        ],
    )


@pytest.fixture
def selected_questions() -> list[SelectedQuestion]:
    return [
        SelectedQuestion(question_id=Q_RISK_01, category=QuestionCategory.RISK, text="Risk?", order=1),
        SelectedQuestion(question_id=Q_FOCUS_02, category=QuestionCategory.FOCUS, text="Focus?", order=2),
        SelectedQuestion(question_id=Q_ENERGY_01, category=QuestionCategory.ENERGY, text="Energy?", order=3),
        SelectedQuestion(question_id=Q_LEARNING_01, category=QuestionCategory.LEARNING, text="Learning?", order=4),
        SelectedQuestion(question_id=Q_ACTION_01, category=QuestionCategory.ACTION, text="Action?", order=5),
    ]


async def test_question_handler_returns_one_question_per_category(
    selected_questions: list[SelectedQuestion],
) -> None:
    checkin_id = uuid4()
    checkin = _asked_checkin(checkin_id, selected_questions)
    service = DailyCheckinService(repository=_make_repository(create_return=checkin))
    request = AskCheckinRequest(
        user_id=uuid4(),
        state=RequestState(
            stress_level=4,
            energy_level=2,
            plan_done=2,
            blocker_present=1,
            learning_done=3,
        ),
    )

    response = await service.question_handler(client_data=request)

    assert response.checkin_id == checkin_id
    assert [q.category for q in response.selected_questions] == list(CATEGORIES)
    assert [q.question_id for q in response.selected_questions] == [
        Q_RISK_01,
        Q_FOCUS_02,
        Q_ENERGY_01,
        Q_LEARNING_01,
        Q_ACTION_01,
    ]
    cast(AsyncMock, service.repository.create_checkin).assert_awaited_once()


async def test_question_handler_returns_existing_asked_checkin(
    selected_questions: list[SelectedQuestion],
) -> None:
    checkin_id = uuid4()
    existing = _asked_checkin(checkin_id, selected_questions)
    service = DailyCheckinService(repository=_make_repository(existing_today=existing))
    request = AskCheckinRequest(
        user_id=existing.user_id,
        state=RequestState(
            stress_level=4,
            energy_level=2,
            plan_done=2,
            blocker_present=1,
            learning_done=3,
        ),
    )

    response = await service.question_handler(client_data=request)

    assert response.checkin_id == checkin_id
    cast(AsyncMock, service.repository.create_checkin).assert_not_awaited()


async def test_question_handler_skips_questions_on_cooldown(
    selected_questions: list[SelectedQuestion],
) -> None:
    checkin_id = uuid4()
    checkin = _asked_checkin(checkin_id, selected_questions)
    service = DailyCheckinService(
        repository=_make_repository(
            create_return=checkin,
            usage={Q_ACTION_01: date.today()},
        )
    )
    request = AskCheckinRequest(
        user_id=uuid4(),
        state=RequestState(
            stress_level=4,
            energy_level=2,
            plan_done=2,
            blocker_present=1,
            learning_done=3,
        ),
    )

    response = await service.question_handler(client_data=request)

    action = next(q for q in response.selected_questions if q.category == QuestionCategory.ACTION)
    assert action.question_id == Q_ACTION_02


async def test_answer_handler_persists_and_returns_response(
    selected_questions: list[SelectedQuestion],
) -> None:
    checkin_id = uuid4()
    user_id = uuid4()
    checkin = _asked_checkin(checkin_id, selected_questions, user_id=user_id)
    service = DailyCheckinService(repository=_make_repository(get_return=checkin))
    request = AnswerCheckinRequest(
        checkin_id=checkin_id,
        user_id=user_id,
        answers=[
            AnswerItem(question_id=Q_RISK_01, answer_text="Too many meetings"),
            AnswerItem(question_id=Q_FOCUS_02, answer_text="Did not finish backend task"),
            AnswerItem(question_id=Q_ENERGY_01, answer_text="No breaks"),
            AnswerItem(question_id=Q_LEARNING_01, answer_text="Learned scoring logic"),
            AnswerItem(question_id=Q_ACTION_01, answer_text="Ship ask endpoint"),
        ],
    )

    response = await service.answer_handler(question_data=request)

    assert response.checkin_id == checkin_id
    assert response.insights.top_risk_or_blocker == "Too many meetings"
    assert checkin.status == CheckinStatus.ANSWERED
    assert checkin.artifact is not None
    cast(AsyncMock, service.repository.save_checkin).assert_awaited_once()


async def test_answer_handler_rejects_mismatched_question_ids(
    selected_questions: list[SelectedQuestion],
) -> None:
    checkin_id = uuid4()
    user_id = uuid4()
    checkin = _asked_checkin(checkin_id, selected_questions, user_id=user_id)
    service = DailyCheckinService(repository=_make_repository(get_return=checkin))
    request = AnswerCheckinRequest(
        checkin_id=checkin_id,
        user_id=user_id,
        answers=[
            AnswerItem(question_id=Q_RISK_01, answer_text="Too many meetings"),
            AnswerItem(question_id=Q_FOCUS_02, answer_text="Did not finish backend task"),
            AnswerItem(question_id=Q_ENERGY_01, answer_text="No breaks"),
            AnswerItem(question_id=Q_LEARNING_01, answer_text="Learned scoring logic"),
            AnswerItem(question_id=Q_ACTION_02, answer_text="Wrong question"),
        ],
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.answer_handler(question_data=request)

    assert exc_info.value.status_code == 422
