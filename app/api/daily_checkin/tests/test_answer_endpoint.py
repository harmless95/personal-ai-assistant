from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.daily_checkin.models.daily import AnswerCheckinRequest, AnswerItem
from app.api.daily_checkin.services.service_daily import DailyCheckinService
from app.main import app

client_test = TestClient(app=app)


def test_answer_daily_checkin_endpoint() -> None:
    payload = {
        "checkin_id": str(uuid4()),
        "answers": [
            {"question_id": "q_risk_01", "answer_text": "Too many meetings"},
            {"question_id": "q_focus_02", "answer_text": "Did not finish backend task"},
            {"question_id": "q_energy_01", "answer_text": "No breaks"},
            {"question_id": "q_learning_01", "answer_text": "Learned scoring logic"},
            {"question_id": "q_action_01", "answer_text": "Ship ask endpoint"},
        ],
    }

    response = client_test.post("/api/v1/daily/checkin/answer/", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["answers_received"] is True
    assert body["checkin_id"] == payload["checkin_id"]
    assert "day_summary" in body
    assert body["insights"]["top_risk_or_blocker"] == "Too many meetings"
    assert body["recommended_actions"]["today_action"] == "Ship ask endpoint"


async def test_answer_handler_builds_summary() -> None:
    checkin_id = uuid4()
    request = AnswerCheckinRequest(
        checkin_id=checkin_id,
        answers=[
            AnswerItem(question_id="q_risk_01", answer_text="Too many meetings"),
            AnswerItem(question_id="q_focus_02", answer_text="Did not finish backend task"),
            AnswerItem(question_id="q_energy_01", answer_text="No breaks"),
            AnswerItem(question_id="q_learning_01", answer_text="Learned scoring logic"),
            AnswerItem(question_id="q_action_01", answer_text="Ship ask endpoint"),
        ],
    )

    response = await DailyCheckinService().answer_handler(question_data=request)

    assert response.checkin_id == checkin_id
    assert response.answers_received is True
    assert "Too many meetings" in response.day_summary
    assert response.insights.top_strength == "Learned scoring logic"
    assert len(response.recommended_actions.two_checkpoints) == 2


async def test_answer_handler_maps_by_category_not_order() -> None:
    checkin_id = uuid4()
    request = AnswerCheckinRequest(
        checkin_id=checkin_id,
        answers=[
            AnswerItem(question_id="q_action_01", answer_text="Ship ask endpoint"),
            AnswerItem(question_id="q_learning_01", answer_text="Learned scoring logic"),
            AnswerItem(question_id="q_energy_01", answer_text="No breaks"),
            AnswerItem(question_id="q_focus_02", answer_text="Did not finish backend task"),
            AnswerItem(question_id="q_risk_01", answer_text="Too many meetings"),
        ],
    )

    response = await DailyCheckinService().answer_handler(question_data=request)

    assert response.insights.top_risk_or_blocker == "Too many meetings"
    assert response.insights.top_strength == "Learned scoring logic"
    assert response.insights.learning_gap == "Learned scoring logic"
    assert response.recommended_actions.today_action == "Ship ask endpoint"
    assert "Too many meetings" in response.day_summary
    assert "Ship ask endpoint" in response.day_summary
