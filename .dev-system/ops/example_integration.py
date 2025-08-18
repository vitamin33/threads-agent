"""
Example Telemetry Integration
Demonstrates how to add telemetry to existing functions
"""

import time
import random
import sys
from pathlib import Path

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

from ops.telemetry import telemetry_decorator


# Example: Simulate model calls with telemetry
@telemetry_decorator(
    agent_name="example_agent",
    event_type="model_call",
    cost_calculator=lambda result: result.get("cost", 0.0),
)
def simulate_openai_call(prompt: str, model: str = "gpt-3.5-turbo"):
    """Simulate an OpenAI API call for testing"""

    # Simulate processing time
    time.sleep(random.uniform(0.1, 2.0))

    # Simulate occasional failures
    if random.random() < 0.1:
        raise Exception("Simulated API failure")

    # Simulate response with usage data
    input_tokens = len(prompt.split()) * 1.3  # Rough token count
    output_tokens = random.randint(50, 200)

    class MockUsage:
        def __init__(self, input_tokens, output_tokens):
            self.prompt_tokens = int(input_tokens)
            self.completion_tokens = int(output_tokens)

    class MockResult:
        def __init__(self, usage, content, cost):
            self.usage = usage
            self.content = content
            self.cost = cost

        def get(self, key, default=None):
            return getattr(self, key, default)

    cost = (input_tokens / 1000 * 0.0015) + (output_tokens / 1000 * 0.002)

    return MockResult(
        usage=MockUsage(input_tokens, output_tokens),
        content=f"Generated response for: {prompt[:50]}...",
        cost=cost,
    )


@telemetry_decorator(agent_name="example_agent", event_type="tool_call")
def simulate_tool_call(tool_name: str, params: dict):
    """Simulate a tool call for testing"""

    # Simulate tool processing
    time.sleep(random.uniform(0.05, 0.5))

    # Simulate occasional tool failures
    if random.random() < 0.05:
        raise Exception(f"Tool {tool_name} failed")

    return {
        "tool": tool_name,
        "result": f"Processed {len(params)} parameters",
        "success": True,
    }


def generate_sample_data(num_calls: int = 10):
    """Generate sample telemetry data for testing"""
    print(f"🔄 Generating {num_calls} sample telemetry events...")

    success_count = 0

    for i in range(num_calls):
        try:
            # Mix of model calls and tool calls
            if i % 3 == 0:
                simulate_tool_call(
                    tool_name=random.choice(["search", "analyze", "format"]),
                    params={"param1": "value", "param2": 123},
                )
            else:
                simulate_openai_call(
                    prompt=f"Generate content for test case {i}", model="gpt-3.5-turbo"
                )
            success_count += 1

        except Exception as e:
            print(f"  ❌ Call {i + 1} failed: {e}")

    print(f"✅ Generated {success_count}/{num_calls} successful calls")
    print("📊 Check results with: just metrics-today")


if __name__ == "__main__":
    generate_sample_data(20)
