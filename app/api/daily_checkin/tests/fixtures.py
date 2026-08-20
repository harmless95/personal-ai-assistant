from uuid import UUID

from app.api.daily_checkin.models.daily import QuestionCategory
from app.db import QuestionPool

Q_RISK_01 = UUID("a1111111-1111-4111-8111-111111111101")
Q_RISK_02 = UUID("a1111111-1111-4111-8111-111111111102")
Q_FOCUS_01 = UUID("a1111111-1111-4111-8111-111111111201")
Q_FOCUS_02 = UUID("a1111111-1111-4111-8111-111111111202")
Q_ENERGY_01 = UUID("a1111111-1111-4111-8111-111111111301")
Q_ENERGY_02 = UUID("a1111111-1111-4111-8111-111111111302")
Q_LEARNING_01 = UUID("a1111111-1111-4111-8111-111111111401")
Q_LEARNING_02 = UUID("a1111111-1111-4111-8111-111111111402")
Q_ACTION_01 = UUID("a1111111-1111-4111-8111-111111111501")
Q_ACTION_02 = UUID("a1111111-1111-4111-8111-111111111502")

DEFAULT_POOL = [
    QuestionPool(
        id=Q_RISK_01,
        category=QuestionCategory.RISK,
        text="What is putting the most pressure on you today?",
        weight=1.0,
        trigger_tags=["stress", "blocker"],
        cooldown_days=3,
        is_active=True,
    ),
    QuestionPool(
        id=Q_RISK_02,
        category=QuestionCategory.RISK,
        text="What risk are you currently ignoring?",
        weight=0.8,
        trigger_tags=["stress"],
        cooldown_days=5,
        is_active=True,
    ),
    QuestionPool(
        id=Q_FOCUS_01,
        category=QuestionCategory.FOCUS,
        text="Which one priority task was not completed?",
        weight=1.0,
        trigger_tags=["plan_miss"],
        cooldown_days=3,
        is_active=True,
    ),
    QuestionPool(
        id=Q_FOCUS_02,
        category=QuestionCategory.FOCUS,
        text="What distracted you from your main priorities?",
        weight=0.9,
        trigger_tags=["plan_miss", "blocker"],
        cooldown_days=4,
        is_active=True,
    ),
    QuestionPool(
        id=Q_ENERGY_01,
        category=QuestionCategory.ENERGY,
        text="What drained your energy the most in the last 2-3 hours?",
        weight=1.0,
        trigger_tags=["low_energy"],
        cooldown_days=3,
        is_active=True,
    ),
    QuestionPool(
        id=Q_ENERGY_02,
        category=QuestionCategory.ENERGY,
        text="When did you last take a real break today?",
        weight=0.7,
        trigger_tags=["low_energy"],
        cooldown_days=7,
        is_active=True,
    ),
    QuestionPool(
        id=Q_LEARNING_01,
        category=QuestionCategory.LEARNING,
        text="What new thing did you try today, even if imperfect?",
        weight=0.8,
        trigger_tags=["learning_mid"],
        cooldown_days=3,
        is_active=True,
    ),
    QuestionPool(
        id=Q_LEARNING_02,
        category=QuestionCategory.LEARNING,
        text="Which skill did not work out today?",
        weight=1.0,
        trigger_tags=["learning_low"],
        cooldown_days=4,
        is_active=True,
    ),
    QuestionPool(
        id=Q_ACTION_01,
        category=QuestionCategory.ACTION,
        text="What is one small step you can still take today?",
        weight=1.0,
        trigger_tags=["low_energy", "plan_miss"],
        cooldown_days=2,
        is_active=True,
    ),
    QuestionPool(
        id=Q_ACTION_02,
        category=QuestionCategory.ACTION,
        text="What can you postpone without real damage?",
        weight=0.8,
        trigger_tags=["stress", "plan_miss"],
        cooldown_days=5,
        is_active=True,
    ),
]
