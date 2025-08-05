"""
OpenAI Cost Tracker - Token-level cost tracking for OpenAI API calls.

Minimal implementation to make our TDD tests pass.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional


class OpenAICostTracker:
    """
    Tracks OpenAI API costs with token-level granularity.

    Minimal implementation following TDD principles.
    """

    # Default pricing (as of current OpenAI pricing)
    DEFAULT_PRICING = {
        "gpt-4o": {
            "input_tokens_per_1k": 0.005,  # $0.005 per 1K input tokens
            "output_tokens_per_1k": 0.015,  # $0.015 per 1K output tokens
        },
        "gpt-3.5-turbo-0125": {
            "input_tokens_per_1k": 0.0005,  # $0.0005 per 1K input tokens
            "output_tokens_per_1k": 0.0015,  # $0.0015 per 1K output tokens
        },
    }

    def __init__(self, pricing_config: Optional[Dict[str, Dict[str, float]]] = None):
        """Initialize the OpenAI cost tracker with pricing configuration."""
        self.pricing_config = pricing_config or self.DEFAULT_PRICING

    def calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate the cost for an API call based on token usage."""
        if model not in self.pricing_config:
            raise ValueError(f"Unknown model: {model}")

        pricing = self.pricing_config[model]

        # Calculate cost: (input_tokens / 1000) * input_price + (output_tokens / 1000) * output_price
        input_cost = (input_tokens / 1000) * pricing["input_tokens_per_1k"]
        output_cost = (output_tokens / 1000) * pricing["output_tokens_per_1k"]

        return input_cost + output_cost

    def track_api_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        operation: str,
        persona_id: str,
        post_id: str,
    ) -> Dict[str, Any]:
        """Track an API call and return a cost event."""
        cost_amount = self.calculate_cost(model, input_tokens, output_tokens)

        cost_event = {
            "cost_amount": cost_amount,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "operation": operation,
            "persona_id": persona_id,
            "post_id": post_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_type": "openai_api",
        }

        return cost_event
