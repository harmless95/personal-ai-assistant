import json
from datetime import date
from pathlib import Path
from uuid import uuid4

from app.api.daily_checkin.models.daily import (
    AskCheckinRequest,
    AskCheckinResponse,
    QuestionPoolItem,
    SelectedQuestion,
)
from app.api.daily_checkin.utils.check_tag import state_to_tags

QUESTIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "questions.json"
CATEGORIES = ["RISK", "FOCUS", "ENERGY", "LEARNING", "ACTION"]


def load_questions() -> list[QuestionPoolItem]:
    with QUESTIONS_PATH.open(encoding="utf-8") as f:
        raw_questions: list[object] = json.load(f)
    return [QuestionPoolItem.model_validate(item) for item in raw_questions]


def score_question(question: QuestionPoolItem, tags: set[str]) -> float:
    matches = len(set(question.trigger_tags) & tags)
    return question.weight * matches


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
