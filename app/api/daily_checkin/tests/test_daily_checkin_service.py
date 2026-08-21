from datetime import date
from typing import Any, cast
from unittest.mock import AsyncMock, Mock, patch
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


def _service(repository: Any) -> DailyCheckinService:
    return DailyCheckinService(repository=repository)


def _make_repository(
    *,
    create_return: DailyCheckin | None = None,
    get_return: DailyCheckin | None = None,
    existing_today: DailyCheckin | None = None,
    history_return: list[DailyCheckin] | None = None,
    pool: list[QuestionPool] | None = None,
    usage: dict[Any, date] | None = None,
) -> Any:
    repository = Mock()
    repository.list_active_questions = AsyncMock(return_value=pool if pool is not None else DEFAULT_POOL)
    repository.list_recent_question_usage = AsyncMock(return_value=(usage if usage is not None else {}, date.today()))
    repository.get_today_checkin = AsyncMock(return_value=existing_today)
    repository.create_checkin = AsyncMock(return_value=create_return)
    repository.get_checkin_by_id = AsyncMock(return_value=get_return)
    repository.list_checkins_by_user = AsyncMock(return_value=history_return or [])
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
    user_id = uuid4()
    checkin = _asked_checkin(checkin_id, selected_questions, user_id=user_id)
    service = _service(_make_repository(create_return=checkin))
    request = AskCheckinRequest(
        state=RequestState(
            stress_level=4,
            energy_level=2,
            plan_done=2,
            blocker_present=1,
            learning_done=3,
        ),
    )

    response = await service.question_handler(client_data=request, user_id=user_id)

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
    service = _service(_make_repository(existing_today=existing))
    request = AskCheckinRequest(
        state=RequestState(
            stress_level=4,
            energy_level=2,
            plan_done=2,
            blocker_present=1,
            learning_done=3,
        ),
    )

    response = await service.question_handler(client_data=request, user_id=existing.user_id)

    assert response.checkin_id == checkin_id
    cast(AsyncMock, service.repository.create_checkin).assert_not_awaited()


async def test_question_handler_skips_questions_on_cooldown(
    selected_questions: list[SelectedQuestion],
) -> None:
    checkin_id = uuid4()
    user_id = uuid4()
    checkin = _asked_checkin(checkin_id, selected_questions, user_id=user_id)
    service = _service(
        _make_repository(
            create_return=checkin,
            usage={Q_ACTION_01: date.today()},
        )
    )
    request = AskCheckinRequest(
        state=RequestState(
            stress_level=4,
            energy_level=2,
            plan_done=2,
            blocker_present=1,
            learning_done=3,
        ),
    )

    response = await service.question_handler(client_data=request, user_id=user_id)

    action = next(q for q in response.selected_questions if q.category == QuestionCategory.ACTION)
    assert action.question_id == Q_ACTION_02


async def test_answer_handler_persists_and_returns_response(
    selected_questions: list[SelectedQuestion],
) -> None:
    checkin_id = uuid4()
    user_id = uuid4()
    checkin = _asked_checkin(checkin_id, selected_questions, user_id=user_id)
    service = _service(_make_repository(get_return=checkin))
    request = AnswerCheckinRequest(
        checkin_id=checkin_id,
        answers=[
            AnswerItem(question_id=Q_RISK_01, answer_text="Too many meetings"),
            AnswerItem(question_id=Q_FOCUS_02, answer_text="Did not finish backend task"),
            AnswerItem(question_id=Q_ENERGY_01, answer_text="No breaks"),
            AnswerItem(question_id=Q_LEARNING_01, answer_text="Learned scoring logic"),
            AnswerItem(question_id=Q_ACTION_01, answer_text="Ship ask endpoint"),
        ],
    )

    with patch(
        "app.api.daily_checkin.services.service_daily.enqueue_day_summary",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_enqueue:
        response = await service.answer_handler(question_data=request, user_id=user_id)

    assert response.checkin_id == checkin_id
    assert response.insights.top_risk_or_blocker == "Too many meetings"
    assert checkin.status == CheckinStatus.ANSWERED
    assert checkin.artifact is None
    cast(AsyncMock, service.repository.save_checkin).assert_awaited_once()
    mock_enqueue.assert_awaited_once_with(str(checkin_id))


async def test_answer_handler_rejects_mismatched_question_ids(
    selected_questions: list[SelectedQuestion],
) -> None:
    checkin_id = uuid4()
    user_id = uuid4()
    checkin = _asked_checkin(checkin_id, selected_questions, user_id=user_id)
    service = _service(_make_repository(get_return=checkin))
    request = AnswerCheckinRequest(
        checkin_id=checkin_id,
        answers=[
            AnswerItem(question_id=Q_RISK_01, answer_text="Too many meetings"),
            AnswerItem(question_id=Q_FOCUS_02, answer_text="Did not finish backend task"),
            AnswerItem(question_id=Q_ENERGY_01, answer_text="No breaks"),
            AnswerItem(question_id=Q_LEARNING_01, answer_text="Learned scoring logic"),
            AnswerItem(question_id=Q_ACTION_02, answer_text="Wrong question"),
        ],
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.answer_handler(question_data=request, user_id=user_id)

    assert exc_info.value.status_code == 422


async def test_history_handler_returns_items(
    selected_questions: list[SelectedQuestion],
) -> None:
    user_id = uuid4()
    checkin = _asked_checkin(uuid4(), selected_questions, user_id=user_id)
    service = _service(_make_repository(history_return=[checkin]))

    response = await service.history_handler(user_id=user_id, limit=30, offset=0)

    assert len(response.items) == 1
    assert response.items[0].checkin_id == checkin.id
    assert response.items[0].status == CheckinStatus.ASKED
    cast(AsyncMock, service.repository.list_checkins_by_user).assert_awaited_once_with(
        user_id=user_id,
        limit=30,
        offset=0,
    )


async def test_artifact_handler_returns_summary(
    selected_questions: list[SelectedQuestion],
) -> None:
    from app.db import DailyArtifact

    checkin_id = uuid4()
    user_id = uuid4()
    checkin = _asked_checkin(checkin_id, selected_questions, user_id=user_id)
    checkin.status = CheckinStatus.ANSWERED
    checkin.artifact = DailyArtifact(
        structured_summary_json={
            "day_summary": "Done",
            "insights": {
                "top_risk_or_blocker": "Meetings",
                "top_strength": "Learning",
                "learning_gap": "Learning",
            },
            "recommended_actions": {
                "today_action": "Ship",
                "two_checkpoints": ["A", "B"],
            },
        }
    )
    service = _service(_make_repository(get_return=checkin))

    response = await service.artifact_handler(checkin_id=checkin_id, user_id=user_id)

    assert response.checkin_id == checkin_id
    assert response.day_summary == "Done"
    assert response.insights.top_risk_or_blocker == "Meetings"
    assert response.recommended_actions.today_action == "Ship"


async def test_artifact_handler_missing_artifact(
    selected_questions: list[SelectedQuestion],
) -> None:
    checkin_id = uuid4()
    user_id = uuid4()
    checkin = _asked_checkin(checkin_id, selected_questions, user_id=user_id)
    checkin.artifact = None
    service = _service(_make_repository(get_return=checkin))

    with pytest.raises(HTTPException) as exc_info:
        await service.artifact_handler(checkin_id=checkin_id, user_id=user_id)

    assert exc_info.value.status_code == 404
    detail = exc_info.value.detail
    assert isinstance(detail, dict)
    assert detail["code"] == "artifact_not_found"
