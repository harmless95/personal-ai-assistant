from app.api.daily_checkin.models.daily import QuestionPoolItem
from app.api.daily_checkin.utils.questions import score_question


def test_score_question_counts_matching_tags() -> None:
    question = QuestionPoolItem(
        id="q_risk_01",
        category="RISK",
        text="What is putting the most pressure on you today?",
        weight=1.0,
        trigger_tags=["stress", "blocker"],
        cooldown_days=3,
    )

    assert score_question(question, {"stress", "blocker"}) == 2.0
    assert score_question(question, {"stress"}) == 1.0
    assert score_question(question, {"learning_mid"}) == 0.0
