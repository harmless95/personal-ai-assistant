from collections.abc import Mapping, Sequence
from datetime import date
from uuid import UUID

from app.api.daily_checkin.models.daily import QuestionCategory, QuestionPoolItem, SelectedQuestion
from app.db import DailyQuestion, QuestionPool

CATEGORIES: tuple[QuestionCategory, ...] = tuple(QuestionCategory)


def to_question_pool_item(question: QuestionPool) -> QuestionPoolItem:
    return QuestionPoolItem(
        id=question.id,
        category=QuestionCategory(question.category),
        text=question.text,
        weight=question.weight,
        trigger_tags=list(question.trigger_tags),
        cooldown_days=question.cooldown_days,
    )


def to_selected_question(question: DailyQuestion) -> SelectedQuestion:
    return SelectedQuestion(
        question_id=question.question_id,
        category=QuestionCategory(question.category),
        text=question.text,
        order=question.sort_order,
    )


def score_question(question: QuestionPoolItem, tags: set[str]) -> float:
    matches = len(set(question.trigger_tags) & tags)
    return question.weight * matches


def blocked_by_cooldown(
    pool: Sequence[QuestionPoolItem],
    last_used_on: Mapping[UUID, date],
    *,
    today: date,
) -> set[UUID]:
    blocked: set[UUID] = set()
    for question in pool:
        used_on = last_used_on.get(question.id)
        if used_on is None:
            continue
        if (today - used_on).days < question.cooldown_days:
            blocked.add(question.id)
    return blocked


def select_questions(
    pool: Sequence[QuestionPoolItem],
    tags: set[str],
    *,
    cooldown_blocked: set[UUID] | None = None,
) -> list[SelectedQuestion] | None:
    """Pick one best question per category. Returns None if any category is missing."""
    blocked = cooldown_blocked or set()
    by_category: dict[QuestionCategory, list[QuestionPoolItem]] = {}
    for question in pool:
        by_category.setdefault(question.category, []).append(question)

    if any(category not in by_category for category in CATEGORIES):
        return None

    selected: list[SelectedQuestion] = []
    for order, category in enumerate(CATEGORIES, start=1):
        candidates = [q for q in by_category[category] if q.id not in blocked]
        if not candidates:
            candidates = by_category[category]
        best = max(candidates, key=lambda q: score_question(q, tags))
        selected.append(
            SelectedQuestion(
                question_id=best.id,
                category=best.category,
                text=best.text,
                order=order,
            )
        )
    return selected
