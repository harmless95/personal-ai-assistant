from unittest.mock import MagicMock

from app.tasks.components.utils.llm_metrics import estimate_cost_usd, extract_token_usage


def test_extract_token_usage_returns_values() -> None:
    completion = MagicMock()
    completion.usage.prompt_tokens = 120
    completion.usage.completion_tokens = 80
    completion.usage.total_tokens = 200

    assert extract_token_usage(completion) == (120, 80, 200)


def test_extract_token_usage_returns_none_without_usage() -> None:
    completion = MagicMock()
    completion.usage = None

    assert extract_token_usage(completion) == (None, None, None)


def test_estimate_cost_usd() -> None:
    cost = estimate_cost_usd(
        prompt_tokens=1_000_000,
        completion_tokens=500_000,
        input_price_per_1m_tokens=0.40,
        output_price_per_1m_tokens=1.60,
    )

    assert cost == 1.2


def test_estimate_cost_usd_returns_none_without_tokens() -> None:
    assert (
        estimate_cost_usd(
            prompt_tokens=None,
            completion_tokens=None,
            input_price_per_1m_tokens=0.40,
            output_price_per_1m_tokens=1.60,
        )
        is None
    )
