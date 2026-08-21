from datetime import date
from uuid import uuid4

from app.api.daily_checkin.models.daily import (
    AnswerItem,
    CheckinStatus,
    QuestionCategory,
    RequestState,
    SelectedQuestion,
)
from app.api.daily_checkin.tests.fixtures import Q_ACTION_01, Q_RISK_01
from app.api.daily_checkin.utils.checkin import (
    attach_answers_and_artifact,
    build_asked_checkin,
    to_artifact_response,
    to_history_item,
)
from app.db import DailyArtifact, DailyCheckin


def test_build_asked_checkin() -> None:
    user_id = uuid4()
    checkin = build_asked_checkin(
        user_id=user_id,
        state=RequestState(
            stress_level=4,
            energy_level=2,
            plan_done=2,
            blocker_present=1,
            learning_done=3,
        ),
        questions=[
            SelectedQuestion(question_id=Q_RISK_01, category=QuestionCategory.RISK, text="Risk?", order=1),
            SelectedQuestion(question_id=Q_ACTION_01, category=QuestionCategory.ACTION, text="Action?", order=2),
        ],
    )

    assert checkin.user_id == user_id
    assert checkin.status == CheckinStatus.ASKED
    assert len(checkin.questions) == 2
    assert checkin.questions[0].question_id == Q_RISK_01
    assert checkin.questions[0].sort_order == 1


def test_attach_answers_and_artifact() -> None:
    checkin = build_asked_checkin(
        user_id=uuid4(),
        state=RequestState(
            stress_level=3,
            energy_level=3,
            plan_done=3,
            blocker_present=0,
            learning_done=3,
        ),
        questions=[
            SelectedQuestion(question_id=Q_RISK_01, category=QuestionCategory.RISK, text="Risk?", order=1),
        ],
    )

    attach_answers_and_artifact(
        checkin,
        answers=[AnswerItem(question_id=Q_RISK_01, answer_text="Meetings")],
        structured_summary={"day_summary": "ok"},
    )

    assert checkin.status == CheckinStatus.ANSWERED
    assert len(checkin.answers) == 1
    assert checkin.answers[0].answer_text == "Meetings"
    assert checkin.artifact is not None
    assert checkin.artifact.structured_summary_json == {"day_summary": "ok"}


def test_to_history_item() -> None:
    checkin_id = uuid4()
    checkin = DailyCheckin(
        id=checkin_id,
        user_id=uuid4(),
        checkin_date=date.today(),
        status=CheckinStatus.ASKED,
        stress_level=3,
        energy_level=3,
        plan_done=3,
        blocker_present=0,
        learning_done=3,
    )

    item = to_history_item(checkin)

    assert item.checkin_id == checkin_id
    assert item.date == checkin.checkin_date
    assert item.status == CheckinStatus.ASKED


def test_to_artifact_response() -> None:
    checkin_id = uuid4()
    checkin = DailyCheckin(
        id=checkin_id,
        user_id=uuid4(),
        checkin_date=date.today(),
        status=CheckinStatus.ANSWERED,
        stress_level=3,
        energy_level=3,
        plan_done=3,
        blocker_present=0,
        learning_done=3,
        artifact=DailyArtifact(
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
        ),
    )

    response = to_artifact_response(checkin)

    assert response.checkin_id == checkin_id
    assert response.day_summary == "Done"
    assert response.insights.top_risk_or_blocker == "Meetings"
    assert response.recommended_actions.today_action == "Ship"
