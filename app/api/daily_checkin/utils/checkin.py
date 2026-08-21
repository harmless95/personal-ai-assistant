from collections.abc import Sequence
from typing import Any
from uuid import UUID

from app.api.daily_checkin.models.daily import (
    AnswerItem,
    ArtifactResponse,
    CheckinStatus,
    DayInsights,
    HistoryItem,
    RecommendedActions,
    RequestState,
    SelectedQuestion,
)
from app.db import DailyArtifact, DailyCheckin, DailyQuestion, QuestionAnswer


def build_asked_checkin(
    *,
    user_id: UUID,
    state: RequestState,
    questions: Sequence[SelectedQuestion],
) -> DailyCheckin:
    return DailyCheckin(
        user_id=user_id,
        status=CheckinStatus.ASKED,
        stress_level=state.stress_level,
        energy_level=state.energy_level,
        plan_done=state.plan_done,
        blocker_present=state.blocker_present,
        learning_done=state.learning_done,
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


def attach_answers(
    checkin: DailyCheckin,
    *,
    answers: Sequence[AnswerItem],
) -> None:
    checkin.status = CheckinStatus.ANSWERED
    checkin.answers = [
        QuestionAnswer(question_id=answer.question_id, answer_text=answer.answer_text) for answer in answers
    ]


def attach_artifact(
    checkin: DailyCheckin,
    *,
    structured_summary: dict[str, Any],
) -> None:
    checkin.artifact = DailyArtifact(structured_summary_json=structured_summary)


def attach_answers_and_artifact(
    checkin: DailyCheckin,
    *,
    answers: Sequence[AnswerItem],
    structured_summary: dict[str, Any],
) -> None:
    attach_answers(checkin, answers=answers)
    attach_artifact(checkin, structured_summary=structured_summary)


def answers_match_questions(
    questions: Sequence[DailyQuestion],
    answers: Sequence[AnswerItem],
) -> bool:
    expected = {question.question_id for question in questions}
    received = {answer.question_id for answer in answers}
    return expected == received


def to_history_item(checkin: DailyCheckin) -> HistoryItem:
    return HistoryItem(
        checkin_id=checkin.id,
        date=checkin.checkin_date,
        status=CheckinStatus(checkin.status),
    )


def to_artifact_response(checkin: DailyCheckin) -> ArtifactResponse:
    if checkin.artifact is None:
        raise ValueError("checkin has no artifact")

    summary = checkin.artifact.structured_summary_json
    return ArtifactResponse(
        checkin_id=checkin.id,
        date=checkin.checkin_date,
        day_summary=summary["day_summary"],
        insights=DayInsights.model_validate(summary["insights"]),
        recommended_actions=RecommendedActions.model_validate(summary["recommended_actions"]),
    )
