from typing import Any


def extract_token_usage(completion: Any) -> tuple[int | None, int | None, int | None]:
    usage = getattr(completion, "usage", None)
    if usage is None:
        return None, None, None
    prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)
    return prompt_tokens, completion_tokens, total_tokens


def estimate_cost_usd(
    *,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    input_price_per_1m_tokens: float,
    output_price_per_1m_tokens: float,
) -> float | None:
    if prompt_tokens is None and completion_tokens is None:
        return None
    prompt = prompt_tokens or 0
    completion = completion_tokens or 0
    return (prompt * input_price_per_1m_tokens + completion * output_price_per_1m_tokens) / 1_000_000
