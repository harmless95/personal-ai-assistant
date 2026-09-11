from collections.abc import Mapping, Sequence
from time import perf_counter
from typing import Any, Literal
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
from app.knowledge.models import KnowledgeChunkHit
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


class ChatCompletionsDaySummaryClient(DaySummaryClient):
    """Shared chat-completions client for OpenAI, Ollama, and similar APIs."""

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
        knowledge_chunks: Sequence[KnowledgeChunkHit] = (),
    ) -> DaySummaryBuildResult:
        fallback = build_answer_response(
            checkin_id=checkin_id,
            answers_by_category=dict(answers_by_category),
        )
        if not self._enabled or self._client is None:
            return self._fallback_result(
                fallback=fallback,
                checkin_id=checkin_id,
                outcome=DaySummaryLlmOutcome.SKIPPED,
                event="day_summary_llm_skipped",
                level="info",
                reason="disabled_or_missing_config",
            )

        user_prompt = self._build_user_prompt(
            questions,
            answers_by_category,
            knowledge_chunks=knowledge_chunks,
        )
        started_at = perf_counter()
        try:
            chat_completion = await self._create_chat_completion(user_prompt)
        except OpenAIError:
            return self._fallback_result(
                fallback=fallback,
                checkin_id=checkin_id,
                outcome=DaySummaryLlmOutcome.REQUEST_FAILED,
                event="day_summary_llm_request_failed",
                exc_info=True,
                latency_ms=(perf_counter() - started_at) * 1000,
            )

        latency_ms = (perf_counter() - started_at) * 1000
        prompt_tokens, completion_tokens, total_tokens = extract_token_usage(chat_completion)
        estimated_cost_usd = estimate_cost_usd(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            input_price_per_1m_tokens=self._input_price_per_1m_tokens,
            output_price_per_1m_tokens=self._output_price_per_1m_tokens,
        )
        usage_kwargs: dict[str, Any] = {
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost_usd,
        }

        content = chat_completion.choices[0].message.content
        if not content:
            return self._fallback_result(
                fallback=fallback,
                checkin_id=checkin_id,
                outcome=DaySummaryLlmOutcome.EMPTY_RESPONSE,
                event="day_summary_llm_empty_response",
                **usage_kwargs,
            )

        try:
            payload = LlmDaySummaryPayload.model_validate_json(content)
        except ValidationError:
            return self._fallback_result(
                fallback=fallback,
                checkin_id=checkin_id,
                outcome=DaySummaryLlmOutcome.INVALID_PAYLOAD,
                event="day_summary_llm_invalid_payload",
                exc_info=True,
                **usage_kwargs,
            )

        metrics = self._build_metrics(outcome=DaySummaryLlmOutcome.LLM_OK, **usage_kwargs)
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

    async def _create_chat_completion(self, user_prompt: str) -> Any:
        assert self._client is not None
        return await self._client.chat.completions.create(
            model=self._model,
            temperature=0.3,
            response_format={"type": "json_object"},
            max_completion_tokens=self._max_completion_tokens,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

    def _fallback_result(
        self,
        *,
        fallback: AnswerCheckinResponse,
        checkin_id: UUID,
        outcome: DaySummaryLlmOutcome,
        event: str,
        level: Literal["info", "warning"] = "warning",
        exc_info: bool = False,
        reason: str | None = None,
        latency_ms: float | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        estimated_cost_usd: float | None = None,
    ) -> DaySummaryBuildResult:
        metrics = self._build_metrics(
            outcome=outcome,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost_usd,
        )
        log_method = logger.info if level == "info" else logger.warning
        log_kwargs: dict[str, Any] = {
            "checkin_id": str(checkin_id),
            **metrics.as_log_fields(),
        }
        if reason is not None:
            log_kwargs["reason"] = reason
        if exc_info:
            log_kwargs["exc_info"] = True
        log_method(event, **log_kwargs)
        return DaySummaryBuildResult(
            response=fallback,
            source=ArtifactSource.TEMPLATE,
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
        *,
        knowledge_chunks: Sequence[KnowledgeChunkHit] = (),
    ) -> str:
        lines = ["Daily check-in answers:"]
        ordered = sorted(questions, key=lambda question: question.sort_order)
        for question in ordered:
            category = QuestionCategory(question.category)
            answer = answers_by_category.get(category, "")
            lines.append(f"- [{category.value}] Q: {question.text}")
            lines.append(f"  A: {answer}")
        if knowledge_chunks:
            lines.append("")
            lines.append("Context from knowledge base:")
            for chunk in knowledge_chunks:
                lines.append(f"- ({chunk.source}) {chunk.text}")
        return "\n".join(lines)
