from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client_test = TestClient(app=app)


def test_ask_daily_checkin_endpoint() -> None:
    payload = {
        "user_id": str(uuid4()),
        "state": {
            "stress_level": 4,
            "energy_level": 2,
            "plan_done": 2,
            "blocker_present": 1,
            "learning_done": 3,
        },
    }

    response = client_test.post("/api/v1/daily/checkin/ask/", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert "checkin_id" in body
    assert "date" in body
    assert len(body["selected_questions"]) == 5
    assert [q["category"] for q in body["selected_questions"]] == [
        "RISK",
        "FOCUS",
        "ENERGY",
        "LEARNING",
        "ACTION",
    ]
    assert [q["question_id"] for q in body["selected_questions"]] == [
        "q_risk_01",
        "q_focus_02",
        "q_energy_01",
        "q_learning_01",
        "q_action_01",
    ]


def test_ask_daily_checkin_validation_error() -> None:
    payload = {
        "user_id": str(uuid4()),
        "state": {
            "stress_level": 9,
            "energy_level": 2,
            "plan_done": 2,
            "blocker_present": 1,
            "learning_done": 3,
        },
    }

    response = client_test.post("/api/v1/daily/checkin/ask/", json=payload)

    assert response.status_code == 422
