from collections.abc import Mapping, Sequence
from uuid import UUID

import structlog
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.api.daily_checkin.models.daily import (
    AnswerCheckinResponse,
    DayInsights,
    QuestionCategory,
    RecommendedActions,
)
from app.api.daily_checkin.utils.summary import build_answer_response
from app.config import settings
from app.db import DailyQuestion
from app.tasks.components.clients.base import DaySummaryClient
from app.tasks.components.prompts.system_prompts import SYSTEM_PROMPT

logger = structlog.get_logger(__name__)


class LlmDaySummaryPayload(BaseModel):
    day_summary: str = Field(min_length=1)
    insights: DayInsights
    recommended_actions: RecommendedActions

    @field_validator("recommended_actions")
    @classmethod
    def validate_checkpoints(cls, value: RecommendedActions) -> RecommendedActions:
        if len(value.two_checkpoints) != 2:
            raise ValueError("two_checkpoints must contain exactly 2 items")
        if any(not item.strip() for item in value.two_checkpoints):
            raise ValueError("two_checkpoints items must be non-empty")
        return value


class OpenAIDaySummaryClient(DaySummaryClient):
    def __init__(self) -> None:
        self._api_key = settings.openai.api_key.get_secret_value().strip()
        self._enabled = settings.openai.enabled and bool(self._api_key)
        self._model = settings.openai.model
        self._max_completion_tokens = settings.openai.max_completion_tokens
        self._client = AsyncOpenAI(api_key=self._api_key) if self._enabled else None

    async def build(
        self,
        *,
        checkin_id: UUID,
        questions: Sequence[DailyQuestion],
        answers_by_category: Mapping[QuestionCategory, str],
    ) -> AnswerCheckinResponse:
        fallback = build_answer_response(
            checkin_id=checkin_id,
            answers_by_category=dict(answers_by_category),
        )
        if not self._enabled or self._client is None:
            logger.info("day_summary_llm_skipped", reason="disabled_or_missing_api_key")
            return fallback

        user_prompt = self._build_user_prompt(questions, answers_by_category)
        try:
            chat_completion = await self._client.chat.completions.create(
                model=self._model,
                temperature=0.3,
                response_format={"type": "json_object"},
                max_completion_tokens=self._max_completion_tokens,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except OpenAIError:
            # Handled degradation: template fallback — not a task failure.
            logger.warning("day_summary_llm_request_failed", checkin_id=str(checkin_id), exc_info=True)
            return fallback

        content = chat_completion.choices[0].message.content
        if not content:
            logger.warning("day_summary_llm_empty_response", checkin_id=str(checkin_id))
            return fallback

        try:
            payload = LlmDaySummaryPayload.model_validate_json(content)
        except ValidationError:
            # Handled degradation: template fallback — do not use exception/error.
            logger.warning("day_summary_llm_invalid_payload", checkin_id=str(checkin_id), exc_info=True)
            return fallback

        logger.info("day_summary_llm_ok", checkin_id=str(checkin_id), model=self._model)
        return AnswerCheckinResponse(
            checkin_id=checkin_id,
            answers_received=True,
            day_summary=payload.day_summary,
            insights=payload.insights,
            recommended_actions=payload.recommended_actions,
        )

    @staticmethod
    def _build_user_prompt(
        questions: Sequence[DailyQuestion],
        answers_by_category: Mapping[QuestionCategory, str],
    ) -> str:
        lines = ["Daily check-in answers:"]
        ordered = sorted(questions, key=lambda question: question.sort_order)
        for question in ordered:
            category = QuestionCategory(question.category)
            answer = answers_by_category.get(category, "")
            lines.append(f"- [{category.value}] Q: {question.text}")
            lines.append(f"  A: {answer}")
        return "\n".join(lines)
