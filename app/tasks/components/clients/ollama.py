from app.config import settings
from app.tasks.components.clients.chat_completions import ChatCompletionsDaySummaryClient
from app.tasks.components.providers import DaySummaryProvider


class OllamaDaySummaryClient(ChatCompletionsDaySummaryClient):
    """Day summary via Ollama's chat-completions /v1 API."""

    def __init__(self) -> None:
        cfg = settings.ollama_llm
        super().__init__(
            provider=DaySummaryProvider.OLLAMA.value,
            api_key=cfg.api_key.get_secret_value().strip() or "ollama",
            model=cfg.model,
            max_completion_tokens=cfg.max_completion_tokens,
            enabled=cfg.enabled,
            input_price_per_1m_tokens=cfg.input_price_per_1m_tokens,
            output_price_per_1m_tokens=cfg.output_price_per_1m_tokens,
            base_url=cfg.base_url,
        )
