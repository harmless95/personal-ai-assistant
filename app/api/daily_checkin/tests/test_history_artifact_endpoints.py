from datetime import date
from typing import Any
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.daily_checkin.deps import get_service
from app.api.daily_checkin.models.daily import CheckinStatus
from app.api.daily_checkin.services.service_daily import DailyCheckinService
from app.db import DailyArtifact, DailyCheckin
from app.main import app

client_test = TestClient(app=app)


def _override_service(service: DailyCheckinService) -> None:
    app.dependency_overrides[get_service] = lambda: service


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def _make_checkin(*, user_id: Any, status: CheckinStatus = CheckinStatus.ASKED) -> DailyCheckin:
    return DailyCheckin(
        id=uuid4(),
        user_id=user_id,
        checkin_date=date.today(),
        status=status,
        stress_level=3,
        energy_level=3,
        plan_done=3,
        blocker_present=0,
        learning_done=3,
    )


def test_get_checkin_history_endpoint() -> None:
    user_id = uuid4()
    checkin = _make_checkin(user_id=user_id)
    repository = Mock()
    repository.list_checkins_by_user = AsyncMock(return_value=[checkin])
    _override_service(DailyCheckinService(repository=repository))

    try:
        response = client_test.get(
            "/api/v1/daily/checkin/history/",
            params={"user_id": str(user_id), "limit": 10, "offset": 0},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["checkin_id"] == str(checkin.id)
    assert body["items"][0]["status"] == "asked"


def test_get_checkin_artifact_endpoint() -> None:
    user_id = uuid4()
    checkin = _make_checkin(user_id=user_id, status=CheckinStatus.ANSWERED)
    checkin.artifact = DailyArtifact(
        structured_summary_json={
            "day_summary": "Done",
            "insights": {
                "top_risk_or_blocker": "Meetings",
                "top_strength": "Learning",
                "learning_gap": "Learning",
            },
            "recommended_actions": {
                "today_action": "Ship",
                "two_checkpoints": ["A", "B"],
            },
        }
    )
    repository = Mock()
    repository.get_checkin_by_id = AsyncMock(return_value=checkin)
    _override_service(DailyCheckinService(repository=repository))

    try:
        response = client_test.get(
            f"/api/v1/daily/checkin/{checkin.id}/artifact/",
            params={"user_id": str(user_id)},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["checkin_id"] == str(checkin.id)
    assert body["day_summary"] == "Done"
    assert body["insights"]["top_risk_or_blocker"] == "Meetings"
