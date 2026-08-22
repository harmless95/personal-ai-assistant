from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.bot.client import ApiClientError, AssistantApiClient
from app.bot.ui import format_artifact, format_history, format_question


def test_format_artifact_ready() -> None:
    text = format_artifact(
        {
            "status": "ready",
            "source": "llm",
            "day_summary": "Solid day.",
            "insights": {
                "top_risk_or_blocker": "Meetings",
                "top_strength": "Focus",
                "learning_gap": "Tests",
            },
            "recommended_actions": {
                "today_action": "Ship bot",
                "two_checkpoints": ["Write tests", "Sleep"],
            },
        }
    )
    assert "Solid day." in text
    assert "Ship bot" in text
    assert "llm" in text


def test_format_artifact_pending() -> None:
    text = format_artifact({"status": "pending"})
    assert "⏳" in text or "готовится" in text.lower()


def test_format_history_empty() -> None:
    text = format_history([])
    assert "пуст" in text.lower()


def test_format_question() -> None:
    text = format_question(1, 5, {"category": "RISK", "text": "What is the risk?"})
    assert "1/5" in text
    assert "RISK" in text
    assert "What is the risk?" in text


@pytest.mark.asyncio
async def test_api_client_login_success(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AssistantApiClient(base_url="http://test", api_prefix="/api/v1")
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.json.return_value = {
        "access_token": "a",
        "refresh_token": "r",
        "token_type": "Bearer",
    }
    mock_post = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(client._client, "post", mock_post)

    result = await client.login(email="u@example.com", password="secret")
    assert result["access_token"] == "a"
    mock_post.assert_awaited_once()
    await client.aclose()


@pytest.mark.asyncio
async def test_api_client_ask_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AssistantApiClient(base_url="http://test")
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.status_code = 409
    mock_response.json.return_value = {
        "detail": {"code": "checkin_exists", "message": "Already exists"},
    }
    mock_response.text = ""
    monkeypatch.setattr(client._client, "post", AsyncMock(return_value=mock_response))

    with pytest.raises(ApiClientError) as exc_info:
        await client.ask_checkin(
            access_token="token",
            state={
                "stress_level": 3,
                "energy_level": 3,
                "plan_done": 3,
                "blocker_present": 0,
                "learning_done": 3,
            },
        )
    assert exc_info.value.status_code == 409
    assert "Already exists" in str(exc_info.value)
    await client.aclose()


@pytest.mark.asyncio
async def test_api_client_get_artifact(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AssistantApiClient(base_url="http://test")
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.json.return_value = {"status": "ready", "day_summary": "ok"}
    mock_get = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(client._client, "get", mock_get)

    result = await client.get_artifact(
        access_token="token",
        checkin_id="11111111-1111-4111-8111-111111111111",
    )
    assert result["status"] == "ready"
    mock_get.assert_awaited_once()
    await client.aclose()


def test_parse_non_json_error() -> None:
    response = MagicMock(spec=httpx.Response)
    response.is_success = False
    response.status_code = 500
    response.json.side_effect = ValueError("no json")
    response.text = "boom"

    with pytest.raises(ApiClientError) as exc_info:
        AssistantApiClient._parse(response)
    assert "boom" in str(exc_info.value)
