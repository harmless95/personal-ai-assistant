from collections.abc import Mapping, Sequence
from uuid import UUID

import structlog
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.api.daily_checkin.models.daily import (
    AnswerCheckinResponse,
    ArtifactSource,
    DayInsights,
    QuestionCategory,
    RecommendedActions,
)
from app.api.daily_checkin.utils.summary import build_answer_response
from app.db import DailyQuestion
from app.tasks.components.clients.base import DaySummaryClient
from app.tasks.components.models.day_summary import DaySummaryBuildResult
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


class OpenAICompatibleDaySummaryClient(DaySummaryClient):
    """Shared chat-completions client for OpenAI and OpenAI-compatible APIs."""

    def __init__(
        self,
        *,
        provider: str,
        api_key: str,
        model: str,
        max_completion_tokens: int,
        enabled: bool,
        base_url: str | None = None,
    ) -> None:
        self._provider = provider
        self._model = model
        self._max_completion_tokens = max_completion_tokens
        self._enabled = enabled
        if not self._enabled:
            self._client = None
        elif base_url:
            self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        else:
            self._client = AsyncOpenAI(api_key=api_key)

    async def build(
        self,
        *,
        checkin_id: UUID,
        questions: Sequence[DailyQuestion],
        answers_by_category: Mapping[QuestionCategory, str],
    ) -> DaySummaryBuildResult:
        fallback = build_answer_response(
            checkin_id=checkin_id,
            answers_by_category=dict(answers_by_category),
        )
        if not self._enabled or self._client is None:
            logger.info(
                "day_summary_llm_skipped",
                provider=self._provider,
                reason="disabled_or_missing_config",
            )
            return DaySummaryBuildResult(response=fallback, source=ArtifactSource.TEMPLATE)

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
            logger.warning(
                "day_summary_llm_request_failed",
                provider=self._provider,
                checkin_id=str(checkin_id),
                exc_info=True,
            )
            return DaySummaryBuildResult(response=fallback, source=ArtifactSource.TEMPLATE)

        content = chat_completion.choices[0].message.content
        if not content:
            logger.warning(
                "day_summary_llm_empty_response",
                provider=self._provider,
                checkin_id=str(checkin_id),
            )
            return DaySummaryBuildResult(response=fallback, source=ArtifactSource.TEMPLATE)

        try:
            payload = LlmDaySummaryPayload.model_validate_json(content)
        except ValidationError:
            logger.warning(
                "day_summary_llm_invalid_payload",
                provider=self._provider,
                checkin_id=str(checkin_id),
                exc_info=True,
            )
            return DaySummaryBuildResult(response=fallback, source=ArtifactSource.TEMPLATE)

        logger.info(
            "day_summary_llm_ok",
            provider=self._provider,
            checkin_id=str(checkin_id),
            model=self._model,
        )
        return DaySummaryBuildResult(
            response=AnswerCheckinResponse(
                checkin_id=checkin_id,
                answers_received=True,
                day_summary=payload.day_summary,
                insights=payload.insights,
                recommended_actions=payload.recommended_actions,
            ),
            source=ArtifactSource.LLM,
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
