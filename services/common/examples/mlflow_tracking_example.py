"""Example of using MLflow tracking in the threads-agent project."""

import asyncio
from services.common.mlflow_tracking import MLflowExperimentTracker, track_llm_call
from services.common.mlflow_openai_wrapper import chat_with_tracking


# Example 1: Direct tracking
def example_direct_tracking():
    """Example of directly tracking an LLM call."""
    print("Example 1: Direct MLflow tracking")

    tracker = MLflowExperimentTracker()
    tracker.track_llm_call(
        persona_id="viral_content_creator",
        model="gpt-4o",
        prompt="Write a viral hook about productivity",
        response="🚀 The ONE morning habit that 10x'd my productivity (and it's not what you think)",
        prompt_tokens=12,
        completion_tokens=25,
        latency_ms=450,
    )
    print("✅ LLM call tracked to MLflow!")


# Example 2: Using the enhanced wrapper
def example_wrapper_tracking():
    """Example of using the enhanced OpenAI wrapper with MLflow tracking."""
    print("\nExample 2: Using enhanced wrapper")

    response = chat_with_tracking(
        model="gpt-3.5-turbo",
        prompt="Generate a business idea in one sentence",
        persona_id="business_strategist",
    )
    print(f"Response: {response}")
    print("✅ Automatically tracked to MLflow!")


# Example 3: Using the decorator (async)
@track_llm_call(persona_id="technical_writer")
async def generate_documentation(topic: str):
    """Example async function that would call OpenAI API."""
    # In real usage, this would call the actual OpenAI API
    # For demo purposes, we'll return a mock response
    from types import SimpleNamespace

    mock_response = SimpleNamespace(
        model="gpt-4o",
        usage=SimpleNamespace(prompt_tokens=15, completion_tokens=50, total_tokens=65),
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=f"# {topic}\n\nThis is a comprehensive guide to {topic}..."
                )
            )
        ],
    )
    return mock_response


async def example_decorator_tracking():
    """Example of using the decorator for automatic tracking."""
    print("\nExample 3: Using decorator for async functions")

    result = await generate_documentation("MLflow Integration")
    print(f"Generated: {result.choices[0].message.content[:50]}...")
    print("✅ Automatically tracked via decorator!")


# Example 4: Batch tracking multiple personas
def example_batch_tracking():
    """Example of tracking multiple LLM calls for different personas."""
    print("\nExample 4: Batch tracking for multiple personas")

    personas = [
        ("tech_influencer", "Write about AI trends"),
        ("fitness_coach", "Create workout motivation"),
        ("food_blogger", "Describe a recipe"),
    ]

    tracker = MLflowExperimentTracker()

    for persona_id, prompt in personas:
        tracker.track_llm_call(
            persona_id=persona_id,
            model="gpt-3.5-turbo",
            prompt=prompt,
            response=f"Generated content for {persona_id}",
            prompt_tokens=10,
            completion_tokens=20,
            latency_ms=200,
        )
        print(f"  ✅ Tracked {persona_id}")


def main():
    """Run all examples."""
    print("🔬 MLflow Tracking Examples for Threads-Agent\n")
    print("=" * 50)

    # Run synchronous examples
    example_direct_tracking()
    example_wrapper_tracking()
    example_batch_tracking()

    # Run async example
    asyncio.run(example_decorator_tracking())

    print("\n" + "=" * 50)
    print("🎉 All examples completed!")
    print("\nTo view the experiments:")
    print("  1. Start MLflow UI: mlflow ui")
    print("  2. Open browser: http://localhost:5000")
    print("  3. Check experiments organized by persona_date")


if __name__ == "__main__":
    main()
