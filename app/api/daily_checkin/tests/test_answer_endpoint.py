from datetime import date
from typing import Any
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.auth.deps import get_current_user
from app.api.daily_checkin.deps import get_service
from app.api.daily_checkin.models.daily import CheckinStatus, QuestionCategory
from app.api.daily_checkin.services.service_daily import DailyCheckinService
from app.api.daily_checkin.tests.fixtures import (
    Q_ACTION_01,
    Q_ENERGY_01,
    Q_FOCUS_02,
    Q_LEARNING_01,
    Q_RISK_01,
)
from app.db import DailyCheckin, DailyQuestion, User
from app.main import app

client_test = TestClient(app=app)


def _override_auth_and_service(user: User, service: DailyCheckinService) -> None:
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_service] = lambda: service


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def _make_user(*, user_id: Any | None = None) -> User:
    return User(
        id=user_id or uuid4(),
        email="user@example.com",
        name="Test",
        surname="User",
        hashed_password="hash",
    )


def _make_asked_checkin(checkin_id: Any, *, user_id: Any) -> DailyCheckin:
    return DailyCheckin(
        id=checkin_id,
        user_id=user_id,
        checkin_date=date.today(),
        status=CheckinStatus.ASKED,
        stress_level=4,
        energy_level=2,
        plan_done=2,
        blocker_present=1,
        learning_done=3,
        questions=[
            DailyQuestion(question_id=Q_RISK_01, category=QuestionCategory.RISK, text="Risk?", sort_order=1),
            DailyQuestion(question_id=Q_FOCUS_02, category=QuestionCategory.FOCUS, text="Focus?", sort_order=2),
            DailyQuestion(question_id=Q_ENERGY_01, category=QuestionCategory.ENERGY, text="Energy?", sort_order=3),
            DailyQuestion(
                question_id=Q_LEARNING_01,
                category=QuestionCategory.LEARNING,
                text="Learning?",
                sort_order=4,
            ),
            DailyQuestion(question_id=Q_ACTION_01, category=QuestionCategory.ACTION, text="Action?", sort_order=5),
        ],
    )


def test_answer_daily_checkin_endpoint() -> None:
    user = _make_user()
    checkin_id = uuid4()
    checkin = _make_asked_checkin(checkin_id, user_id=user.id)
    repository = Mock()
    repository.get_checkin_by_id = AsyncMock(return_value=checkin)
    repository.save_checkin = AsyncMock(return_value=checkin)
    _override_auth_and_service(user, DailyCheckinService(repository=repository))

    payload = {
        "checkin_id": str(checkin_id),
        "answers": [
            {"question_id": str(Q_RISK_01), "answer_text": "Too many meetings"},
            {"question_id": str(Q_FOCUS_02), "answer_text": "Did not finish backend task"},
            {"question_id": str(Q_ENERGY_01), "answer_text": "No breaks"},
            {"question_id": str(Q_LEARNING_01), "answer_text": "Learned scoring logic"},
            {"question_id": str(Q_ACTION_01), "answer_text": "Ship ask endpoint"},
        ],
    }

    try:
        with patch(
            "app.api.daily_checkin.services.service_daily.enqueue_day_summary",
            new_callable=AsyncMock,
            return_value=True,
        ):
            response = client_test.post("/api/v1/daily/checkin/answer/", json=payload)
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["answers_received"] is True
    assert body["checkin_id"] == payload["checkin_id"]
    assert body["insights"]["top_risk_or_blocker"] == "Too many meetings"
    assert body["recommended_actions"]["today_action"] == "Ship ask endpoint"
