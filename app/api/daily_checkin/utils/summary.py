from collections.abc import Sequence
from typing import Any
from uuid import UUID

from app.api.daily_checkin.models.daily import (
    AnswerCheckinResponse,
    AnswerItem,
    DayInsights,
    QuestionCategory,
    RecommendedActions,
)
from app.db import DailyQuestion


def map_answers_by_category(
    questions: Sequence[DailyQuestion],
    answers: Sequence[AnswerItem],
) -> dict[QuestionCategory, str]:
    questions_by_id = {question.question_id: question for question in questions}
    answers_by_category: dict[QuestionCategory, str] = {}

    for answer in answers:
        question = questions_by_id.get(answer.question_id)
        if question is None:
            continue
        answers_by_category[QuestionCategory(question.category)] = answer.answer_text

    return answers_by_category


def build_answer_response(
    checkin_id: UUID,
    answers_by_category: dict[QuestionCategory, str],
) -> AnswerCheckinResponse:
    risk_answer = answers_by_category.get(QuestionCategory.RISK, "")
    learning_answer = answers_by_category.get(QuestionCategory.LEARNING, "")
    action_answer = answers_by_category.get(QuestionCategory.ACTION, "")

    return AnswerCheckinResponse(
        checkin_id=checkin_id,
        answers_received=True,
        day_summary=(
            "You completed today's check-in. "
            f"Main focus from your answers: {risk_answer}. "
            f"Next step mentioned: {action_answer}."
        ),
        insights=DayInsights(
            top_risk_or_blocker=risk_answer,
            top_strength=learning_answer,
            learning_gap=learning_answer,
        ),
        recommended_actions=RecommendedActions(
            today_action=action_answer,
            two_checkpoints=[
                "Review your top blocker once today",
                "Complete one small action from your check-in",
            ],
        ),
    )


def structured_summary_from_response(response: AnswerCheckinResponse) -> dict[str, Any]:
    return {
        "day_summary": response.day_summary,
        "insights": response.insights.model_dump(),
        "recommended_actions": response.recommended_actions.model_dump(),
    }
