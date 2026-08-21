from datetime import date

from app.api.daily_checkin.models.daily import QuestionCategory, QuestionPoolItem
from app.api.daily_checkin.tests.fixtures import (
    DEFAULT_POOL,
    Q_ACTION_01,
    Q_ACTION_02,
    Q_ENERGY_01,
    Q_FOCUS_02,
    Q_LEARNING_01,
    Q_RISK_01,
)
from app.api.daily_checkin.utils.questions import (
    CATEGORIES,
    blocked_by_cooldown,
    score_question,
    select_questions,
    to_question_pool_item,
)


def test_score_question_counts_matching_tags() -> None:
    question = QuestionPoolItem(
        id=Q_RISK_01,
        category=QuestionCategory.RISK,
        text="What is putting the most pressure on you today?",
        weight=1.0,
        trigger_tags=["stress", "blocker"],
        cooldown_days=3,
    )

    assert score_question(question, {"stress", "blocker"}) == 2.0
    assert score_question(question, {"stress"}) == 1.0
    assert score_question(question, {"learning_mid"}) == 0.0


def test_select_questions_picks_best_per_category() -> None:
    selected = select_questions(
        pool=[to_question_pool_item(row) for row in DEFAULT_POOL],
        tags={"stress", "blocker", "plan_miss", "low_energy", "learning_mid"},
    )

    assert selected is not None
    assert [q.category for q in selected] == list(CATEGORIES)
    assert [q.question_id for q in selected] == [
        Q_RISK_01,
        Q_FOCUS_02,
        Q_ENERGY_01,
        Q_LEARNING_01,
        Q_ACTION_01,
    ]


def test_select_questions_returns_none_when_category_missing() -> None:
    incomplete_pool = [to_question_pool_item(row) for row in DEFAULT_POOL if row.category != QuestionCategory.ACTION]
    assert select_questions(pool=incomplete_pool, tags={"stress"}) is None


def test_select_questions_respects_cooldown() -> None:
    pool = [to_question_pool_item(row) for row in DEFAULT_POOL]
    blocked = blocked_by_cooldown(pool, {Q_ACTION_01: date.today()}, today=date.today())
    selected = select_questions(
        pool=pool,
        tags={"stress", "blocker", "plan_miss", "low_energy", "learning_mid"},
        cooldown_blocked=blocked,
    )

    assert selected is not None
    action = next(q for q in selected if q.category == QuestionCategory.ACTION)
    assert action.question_id == Q_ACTION_02
