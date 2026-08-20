from collections.abc import Sequence
from typing import Any
from uuid import UUID

from app.api.daily_checkin.models.daily import AnswerItem, CheckinStatus, RequestState, SelectedQuestion
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


def attach_answers_and_artifact(
    checkin: DailyCheckin,
    *,
    answers: Sequence[AnswerItem],
    structured_summary: dict[str, Any],
) -> None:
    checkin.status = CheckinStatus.ANSWERED
    checkin.answers = [
        QuestionAnswer(question_id=answer.question_id, answer_text=answer.answer_text) for answer in answers
    ]
    checkin.artifact = DailyArtifact(structured_summary_json=structured_summary)


def answers_match_questions(
    questions: Sequence[DailyQuestion],
    answers: Sequence[AnswerItem],
) -> bool:
    expected = {question.question_id for question in questions}
    received = {answer.question_id for answer in answers}
    return expected == received
