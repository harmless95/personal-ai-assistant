from datetime import date
from uuid import uuid4

from app.api.daily_checkin.models.daily import AskCheckinRequest, AskCheckinResponse, SelectedQuestion
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
