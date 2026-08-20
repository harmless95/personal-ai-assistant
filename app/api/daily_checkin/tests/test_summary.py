from uuid import uuid4

from app.api.daily_checkin.models.daily import AnswerItem, QuestionCategory
from app.api.daily_checkin.tests.fixtures import (
    Q_ACTION_01,
    Q_ENERGY_01,
    Q_FOCUS_02,
    Q_LEARNING_01,
    Q_RISK_01,
)
from app.api.daily_checkin.utils.summary import (
    build_answer_response,
    map_answers_by_category,
    structured_summary_from_response,
)
from app.db import DailyQuestion


def _questions() -> list[DailyQuestion]:
    return [
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
    ]


def test_map_answers_by_category_ignores_order() -> None:
    mapped = map_answers_by_category(
        questions=_questions(),
        answers=[
            AnswerItem(question_id=Q_ACTION_01, answer_text="Ship ask endpoint"),
            AnswerItem(question_id=Q_LEARNING_01, answer_text="Learned scoring logic"),
            AnswerItem(question_id=Q_ENERGY_01, answer_text="No breaks"),
            AnswerItem(question_id=Q_FOCUS_02, answer_text="Did not finish backend task"),
            AnswerItem(question_id=Q_RISK_01, answer_text="Too many meetings"),
        ],
    )

    assert mapped[QuestionCategory.RISK] == "Too many meetings"
    assert mapped[QuestionCategory.LEARNING] == "Learned scoring logic"
    assert mapped[QuestionCategory.ACTION] == "Ship ask endpoint"


def test_build_answer_response_summary() -> None:
    checkin_id = uuid4()
    response = build_answer_response(
        checkin_id=checkin_id,
        answers_by_category={
            QuestionCategory.RISK: "Too many meetings",
            QuestionCategory.LEARNING: "Learned scoring logic",
            QuestionCategory.ACTION: "Ship ask endpoint",
        },
    )

    assert response.checkin_id == checkin_id
    assert response.answers_received is True
    assert "Too many meetings" in response.day_summary
    assert response.insights.top_strength == "Learned scoring logic"
    assert response.recommended_actions.today_action == "Ship ask endpoint"
    assert len(response.recommended_actions.two_checkpoints) == 2

    summary = structured_summary_from_response(response)
    assert summary["day_summary"] == response.day_summary
    assert summary["insights"]["top_risk_or_blocker"] == "Too many meetings"
