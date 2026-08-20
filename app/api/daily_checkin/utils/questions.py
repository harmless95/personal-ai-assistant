import json
from pathlib import Path

from app.api.daily_checkin.models.daily import QuestionPoolItem

QUESTIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "questions.json"


def load_questions() -> list[QuestionPoolItem]:
    with QUESTIONS_PATH.open(encoding="utf-8") as f:
        raw_questions: list[object] = json.load(f)
    return [QuestionPoolItem.model_validate(item) for item in raw_questions]


def score_question(question: QuestionPoolItem, tags: set[str]) -> float:
    matches = len(set(question.trigger_tags) & tags)
    return question.weight * matches
