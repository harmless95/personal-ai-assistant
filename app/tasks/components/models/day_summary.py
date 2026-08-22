from dataclasses import dataclass
from enum import StrEnum

from app.api.daily_checkin.models.daily import AnswerCheckinResponse, ArtifactSource


class DaySummaryLlmOutcome(StrEnum):
    SKIPPED = "skipped"
    LLM_OK = "llm_ok"
    REQUEST_FAILED = "request_failed"
    EMPTY_RESPONSE = "empty_response"
    INVALID_PAYLOAD = "invalid_payload"
    TEMPLATE = "template"


@dataclass(frozen=True, slots=True)
class DaySummaryUsageMetrics:
    outcome: DaySummaryLlmOutcome
    provider: str
    model: str | None = None
    latency_ms: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None

    def as_log_fields(self) -> dict[str, object]:
        fields: dict[str, object] = {
            "outcome": self.outcome.value,
            "provider": self.provider,
        }
        if self.model is not None:
            fields["model"] = self.model
        if self.latency_ms is not None:
            fields["latency_ms"] = round(self.latency_ms, 2)
        if self.prompt_tokens is not None:
            fields["prompt_tokens"] = self.prompt_tokens
        if self.completion_tokens is not None:
            fields["completion_tokens"] = self.completion_tokens
        if self.total_tokens is not None:
            fields["total_tokens"] = self.total_tokens
        if self.estimated_cost_usd is not None:
            fields["estimated_cost_usd"] = round(self.estimated_cost_usd, 6)
        return fields


@dataclass(frozen=True, slots=True)
class DaySummaryBuildResult:
    response: AnswerCheckinResponse
    source: ArtifactSource
    metrics: DaySummaryUsageMetrics
