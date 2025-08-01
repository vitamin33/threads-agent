"""MLflow experiment tracking for LLM calls."""

from datetime import datetime
import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar, Awaitable

import mlflow

from services.common.mlflow_config import configure_mlflow

logger = logging.getLogger(__name__)

# Configure MLflow on module import
configure_mlflow()

T = TypeVar("T")


class MLflowExperimentTracker:
    """Tracks LLM experiments using MLflow."""

    def track_llm_call(
        self,
        persona_id: str,
        model: str,
        prompt: str,
        response: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
    ) -> None:
        """Track a single LLM call to MLflow."""
        try:
            # Set experiment name based on persona and date
            date_str = datetime.now().strftime("%Y-%m-%d")
            experiment_name = f"{persona_id}_{date_str}"
            mlflow.set_experiment(experiment_name)

            mlflow.start_run()
            mlflow.log_params(
                {
                    "persona_id": persona_id,
                    "model": model,
                    "prompt": prompt,
                    "response": response,
                }
            )
            mlflow.log_metrics(
                {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "latency_ms": latency_ms,
                }
            )
            mlflow.end_run()
        except Exception as e:
            logger.warning(f"Failed to track LLM call to MLflow: {e}")


def track_llm_call(
    persona_id: str,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator to automatically track LLM calls to MLflow.

    Args:
        persona_id: The persona ID to use for experiment organization

    Returns:
        Decorated function that tracks LLM calls
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()

            # Call the original function
            result = await func(*args, **kwargs)

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Extract LLM call details from result
            # Assuming result has OpenAI-like structure
            model = getattr(result, "model", "unknown")
            usage = getattr(result, "usage", None)

            if usage:
                prompt_tokens = getattr(usage, "prompt_tokens", 0)
                completion_tokens = getattr(usage, "completion_tokens", 0)
            else:
                prompt_tokens = 0
                completion_tokens = 0

            # Extract prompt from args/kwargs
            prompt = ""
            if args and isinstance(args[0], str):
                prompt = args[0]
            elif "prompt" in kwargs:
                prompt = kwargs["prompt"]
            elif "messages" in kwargs:
                # Handle chat completions format
                messages = kwargs["messages"]
                if messages and isinstance(messages, list):
                    prompt = str(messages)

            # Extract response
            response = ""
            if hasattr(result, "choices") and result.choices:
                choice = result.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    response = choice.message.content
                elif hasattr(choice, "text"):
                    response = choice.text

            # Track the call
            tracker = MLflowExperimentTracker()
            tracker.track_llm_call(
                persona_id=persona_id,
                model=model,
                prompt=prompt,
                response=response,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
            )

            return result

        return wrapper

    return decorator
