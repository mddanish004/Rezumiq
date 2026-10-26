"""Model pricing, ported from lib/ai/pricing.ts."""

from __future__ import annotations

PRICES = {
    "gpt-oss-20b": {"input": 0.075, "cached_input": 0.0375, "output": 0.30},
    "gpt-oss-120b": {"input": 0.15, "cached_input": 0.075, "output": 0.60},
    "gpt-5.4-mini": {"input": 0.75, "cached_input": 0.075, "output": 4.5},
    "gpt-5.5": {"input": 5, "cached_input": 0.5, "output": 30},
    "claude-haiku-4-5": {"input": 1, "cached_input": 0.1, "output": 5},
    "claude-sonnet-5": {"input": 2, "cached_input": 0.2, "output": 10},
}


def price_for(model_id: str) -> dict | None:
    return PRICES.get(model_id) or PRICES.get(model_id.split("/")[-1])


def cost_usd_micros(model_id: str, usage: dict) -> int:
    price = price_for(model_id)
    if not price:
        return 0
    uncached = usage.get("input", 0) - usage.get("cached", 0)
    return round(
        uncached * price["input"]
        + usage.get("cached", 0) * price["cached_input"]
        + usage.get("output", 0) * price["output"]
    )


def known_cost_usd_micros(cost: int, input_tokens: int, output_tokens: int) -> int | None:
    """None when tokens were used but nothing was charged: the model had no price when the run was logged."""
    return None if cost == 0 and input_tokens + output_tokens > 0 else cost
