from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from openai import OpenAIError
from pydantic import SecretStr

from app.api.daily_checkin.models.daily import QuestionCategory
from app.config import settings
from app.db import DailyQuestion
from app.tasks.components.clients.openai import OpenAIDaySummaryClient
from app.tasks.components.clients.template import TemplateDaySummaryClient


def _questions() -> list[DailyQuestion]:
    return [
        DailyQuestion(
            question_id=uuid4(),
            category=QuestionCategory.RISK,
            text="What is the risk?",
            sort_order=1,
        ),
        DailyQuestion(
            question_id=uuid4(),
            category=QuestionCategory.FOCUS,
            text="What about focus?",
            sort_order=2,
        ),
        DailyQuestion(
            question_id=uuid4(),
            category=QuestionCategory.ENERGY,
            text="What about energy?",
            sort_order=3,
        ),
        DailyQuestion(
            question_id=uuid4(),
            category=QuestionCategory.LEARNING,
            text="What about learning?",
            sort_order=4,
        ),
        DailyQuestion(
            question_id=uuid4(),
            category=QuestionCategory.ACTION,
            text="What about action?",
            sort_order=5,
        ),
    ]


def _answers() -> dict[QuestionCategory, str]:
    return {
        QuestionCategory.RISK: "Too many meetings",
        QuestionCategory.FOCUS: "Backend unfinished",
        QuestionCategory.ENERGY: "No breaks",
        QuestionCategory.LEARNING: "Learned scoring",
        QuestionCategory.ACTION: "Ship endpoint",
    }


@pytest.mark.asyncio
async def test_template_day_summary_client() -> None:
    checkin_id = uuid4()
    client = TemplateDaySummaryClient()
    response = await client.build(
        checkin_id=checkin_id,
        questions=_questions(),
        answers_by_category=_answers(),
    )
    assert response.checkin_id == checkin_id
    assert "Too many meetings" in response.day_summary
    assert response.recommended_actions.today_action == "Ship endpoint"


@pytest.mark.asyncio
async def test_openai_client_falls_back_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.openai, "enabled", True)
    monkeypatch.setattr(settings.openai, "api_key", SecretStr(""))
    client = OpenAIDaySummaryClient()
    checkin_id = uuid4()
    response = await client.build(
        checkin_id=checkin_id,
        questions=_questions(),
        answers_by_category=_answers(),
    )
    assert "Too many meetings" in response.day_summary


@pytest.mark.asyncio
async def test_openai_client_uses_llm_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.openai, "enabled", True)
    monkeypatch.setattr(settings.openai, "api_key", SecretStr("test-key"))
    monkeypatch.setattr(settings.openai, "model", "gpt-test")
    monkeypatch.setattr(settings.openai, "max_completion_tokens", 256)

    payload = """
    {
      "day_summary": "Meetings drained focus; finish one backend step.",
      "insights": {
        "top_risk_or_blocker": "Meeting overload",
        "top_strength": "Learning scoring",
        "learning_gap": "Need deeper practice"
      },
      "recommended_actions": {
        "today_action": "Ship a small endpoint slice",
        "two_checkpoints": ["Take a break", "Close one task"]
      }
    }
    """
    choice = MagicMock()
    choice.message.content = payload
    completion = MagicMock()
    completion.choices = [choice]

    fake_client = MagicMock()
    fake_client.chat.completions.create = AsyncMock(return_value=completion)

    with patch("app.tasks.components.clients.openai.AsyncOpenAI", return_value=fake_client):
        client = OpenAIDaySummaryClient()
        response = await client.build(
            checkin_id=uuid4(),
            questions=_questions(),
            answers_by_category=_answers(),
        )

    assert response.day_summary.startswith("Meetings drained focus")
    assert response.insights.top_risk_or_blocker == "Meeting overload"
    assert response.recommended_actions.two_checkpoints == ["Take a break", "Close one task"]
    fake_client.chat.completions.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_openai_client_falls_back_on_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings.openai, "enabled", True)
    monkeypatch.setattr(settings.openai, "api_key", SecretStr("test-key"))

    fake_client = MagicMock()
    fake_client.chat.completions.create = AsyncMock(side_effect=OpenAIError("boom"))

    with patch("app.tasks.components.clients.openai.AsyncOpenAI", return_value=fake_client):
        client = OpenAIDaySummaryClient()
        response = await client.build(
            checkin_id=uuid4(),
            questions=_questions(),
            answers_by_category=_answers(),
        )

    assert "Too many meetings" in response.day_summary
