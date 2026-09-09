from collections.abc import Mapping

from app.api.daily_checkin.models.daily import QuestionCategory


def build_knowledge_query(answers_by_category: Mapping[QuestionCategory, str]) -> str:
    """Join check-in answers into a single Search query."""
    parts = [
        text.strip()
        for _, text in sorted(answers_by_category.items(), key=lambda item: item[0].value)
        if text.strip()
    ]
    return " ".join(parts)
