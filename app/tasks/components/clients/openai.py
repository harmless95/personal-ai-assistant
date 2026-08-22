from app.config import settings
from app.tasks.components.clients.openai_compatible import OpenAICompatibleDaySummaryClient
from app.tasks.components.providers import DaySummaryProvider


class OpenAIDaySummaryClient(OpenAICompatibleDaySummaryClient):
    def __init__(self) -> None:
        api_key = settings.openai.api_key.get_secret_value().strip()
        super().__init__(
            provider=DaySummaryProvider.OPENAI.value,
            api_key=api_key,
            model=settings.openai.model,
            max_completion_tokens=settings.openai.max_completion_tokens,
            enabled=settings.openai.enabled and bool(api_key),
            input_price_per_1m_tokens=settings.openai.input_price_per_1m_tokens,
            output_price_per_1m_tokens=settings.openai.output_price_per_1m_tokens,
        )
