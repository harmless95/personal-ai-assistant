from app.api.daily_checkin.models.daily import AskCheckinRequest, QuestionPoolItem, RequestState
from app.api.daily_checkin.services.service_daily import (
    CATEGORIES,
    DailyCheckinService,
    score_question,
)


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


async def test_question_handler_returns_one_question_per_category() -> None:
    service = DailyCheckinService()
    request = AskCheckinRequest(
        user_id=1,
        state=RequestState(
            stress_level=4,
            energy_level=2,
            plan_done=2,
            blocker_present=1,
            learning_done=3,
        ),
    )

    response = await service.question_handler(client_data=request)

    assert len(response.selected_questions) == 5
    assert [q.category for q in response.selected_questions] == CATEGORIES
    assert [q.order for q in response.selected_questions] == [1, 2, 3, 4, 5]
    assert [q.question_id for q in response.selected_questions] == [
        "q_risk_01",
        "q_focus_02",
        "q_energy_01",
        "q_learning_01",
        "q_action_01",
    ]
