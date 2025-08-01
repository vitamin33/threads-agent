"""Enhanced OpenAI wrapper with MLflow tracking integration."""

import time
from services.common import openai_wrapper
from services.common.mlflow_tracking import MLflowExperimentTracker


def chat_with_tracking(model: str, prompt: str, persona_id: str) -> str:
    """Enhanced chat function that tracks LLM calls to MLflow.

    Args:
        model: The OpenAI model to use
        prompt: The prompt to send
        persona_id: The persona ID for experiment organization

    Returns:
        The response text from the LLM
    """
    start_time = time.time()

    # Call the original chat function
    response = openai_wrapper.chat(model, prompt)

    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)

    # Get token count from the cached result
    # The original chat function returns text and caches tokens internally
    # We'll estimate tokens for now (can be enhanced later)
    prompt_tokens = len(prompt.split()) * 2  # Rough estimate
    completion_tokens = len(response.split()) * 2  # Rough estimate

    # Track to MLflow
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

    return response
