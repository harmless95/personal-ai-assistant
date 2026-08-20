from datetime import date
from uuid import uuid4

from app.api.daily_checkin.models.daily import (
    AnswerCheckinRequest,
    AnswerCheckinResponse,
    AskCheckinRequest,
    AskCheckinResponse,
    DayInsights,
    RecommendedActions,
    SelectedQuestion,
)
from app.api.daily_checkin.utils.check_tag import state_to_tags
from app.api.daily_checkin.utils.questions import load_questions, score_question

CATEGORIES = ["RISK", "FOCUS", "ENERGY", "LEARNING", "ACTION"]


class DailyCheckinService:
    async def question_handler(self, client_data: AskCheckinRequest) -> AskCheckinResponse:
        tags = state_to_tags(state=client_data.state)
        questions = load_questions()
        selected: list[SelectedQuestion] = []
        for order, category in enumerate(CATEGORIES, start=1):
            candidates = [q for q in questions if q.category == category]
            best = max(candidates, key=lambda q: score_question(q, tags))
            selected.append(
                SelectedQuestion(
                    question_id=best.id,
                    category=best.category,
                    text=best.text,
                    order=order,
                )
            )
        return AskCheckinResponse(
            checkin_id=uuid4(),
            date=date.today(),
            selected_questions=selected,
        )

    async def answer_handler(self, question_data: AnswerCheckinRequest) -> AnswerCheckinResponse:
        answers_by_category = self._map_answers_by_category(question_data)

        risk_answer = answers_by_category.get("RISK", "")
        learning_answer = answers_by_category.get("LEARNING", "")
        action_answer = answers_by_category.get("ACTION", "")

        return AnswerCheckinResponse(
            checkin_id=question_data.checkin_id,
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

    def _map_answers_by_category(self, question_data: AnswerCheckinRequest) -> dict[str, str]:
        questions_by_id = {question.id: question for question in load_questions()}
        answers_by_category: dict[str, str] = {}

        for answer in question_data.answers:
            question = questions_by_id.get(answer.question_id)
            if question is None:
                continue
            answers_by_category[question.category] = answer.answer_text

        return answers_by_category

