from collections.abc import Mapping, Sequence
from time import perf_counter
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
from app.tasks.components.models.day_summary import (
    DaySummaryBuildResult,
    DaySummaryLlmOutcome,
    DaySummaryUsageMetrics,
)
from app.tasks.components.prompts.system_prompts import SYSTEM_PROMPT
from app.tasks.components.utils.llm_metrics import estimate_cost_usd, extract_token_usage

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
        input_price_per_1m_tokens: float,
        output_price_per_1m_tokens: float,
        base_url: str | None = None,
    ) -> None:
        self._provider = provider
        self._model = model
        self._max_completion_tokens = max_completion_tokens
        self._enabled = enabled
        self._input_price_per_1m_tokens = input_price_per_1m_tokens
        self._output_price_per_1m_tokens = output_price_per_1m_tokens
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
            metrics = DaySummaryUsageMetrics(
                outcome=DaySummaryLlmOutcome.SKIPPED,
                provider=self._provider,
                model=self._model,
            )
            logger.info(
                "day_summary_llm_skipped",
                checkin_id=str(checkin_id),
                reason="disabled_or_missing_config",
                **metrics.as_log_fields(),
            )
            return DaySummaryBuildResult(response=fallback, source=ArtifactSource.TEMPLATE, metrics=metrics)

        user_prompt = self._build_user_prompt(questions, answers_by_category)
        started_at = perf_counter()
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
            metrics = self._build_metrics(
                outcome=DaySummaryLlmOutcome.REQUEST_FAILED,
                latency_ms=(perf_counter() - started_at) * 1000,
            )
            logger.warning(
                "day_summary_llm_request_failed",
                checkin_id=str(checkin_id),
                exc_info=True,
                **metrics.as_log_fields(),
            )
            return DaySummaryBuildResult(response=fallback, source=ArtifactSource.TEMPLATE, metrics=metrics)

        latency_ms = (perf_counter() - started_at) * 1000
        prompt_tokens, completion_tokens, total_tokens = extract_token_usage(chat_completion)
        estimated_cost_usd = estimate_cost_usd(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            input_price_per_1m_tokens=self._input_price_per_1m_tokens,
            output_price_per_1m_tokens=self._output_price_per_1m_tokens,
        )

        content = chat_completion.choices[0].message.content
        if not content:
            metrics = self._build_metrics(
                outcome=DaySummaryLlmOutcome.EMPTY_RESPONSE,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=estimated_cost_usd,
            )
            logger.warning(
                "day_summary_llm_empty_response",
                checkin_id=str(checkin_id),
                **metrics.as_log_fields(),
            )
            return DaySummaryBuildResult(response=fallback, source=ArtifactSource.TEMPLATE, metrics=metrics)

        try:
            payload = LlmDaySummaryPayload.model_validate_json(content)
        except ValidationError:
            metrics = self._build_metrics(
                outcome=DaySummaryLlmOutcome.INVALID_PAYLOAD,
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=estimated_cost_usd,
            )
            logger.warning(
                "day_summary_llm_invalid_payload",
                checkin_id=str(checkin_id),
                exc_info=True,
                **metrics.as_log_fields(),
            )
            return DaySummaryBuildResult(response=fallback, source=ArtifactSource.TEMPLATE, metrics=metrics)

        metrics = self._build_metrics(
            outcome=DaySummaryLlmOutcome.LLM_OK,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost_usd,
        )
        logger.info(
            "day_summary_llm_ok",
            checkin_id=str(checkin_id),
            **metrics.as_log_fields(),
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
            metrics=metrics,
        )

    def _build_metrics(
        self,
        *,
        outcome: DaySummaryLlmOutcome,
        latency_ms: float | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        estimated_cost_usd: float | None = None,
    ) -> DaySummaryUsageMetrics:
        return DaySummaryUsageMetrics(
            outcome=outcome,
            provider=self._provider,
            model=self._model,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost_usd,
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
