"""Test-specific pytest configuration."""

import os
import warnings
import pytest


# Disable langsmith/langchain tracing before any imports
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING"] = "false"
os.environ["LANGCHAIN_CALLBACKS_MANAGER"] = "false"
os.environ["LANGSMITH_API_KEY"] = ""

# Suppress pydantic v1/v2 compatibility warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Skip only truly performance-sensitive tests in CI
def pytest_collection_modifyitems(config, items):
    """Skip performance-sensitive tests in CI environment."""
    if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true":
        skip_ci = pytest.mark.skip(reason="Skipped in CI - performance-sensitive test")
        for item in items:
            # Only skip specific performance/concurrency tests that are timing-sensitive
            if any(x in item.nodeid.lower() for x in [
                "test_concurrent_emotion_analysis_100_threads",
                "test_scalability_stress_test", 
                "test_memory_usage_under_load",
                "test_resource_contention_handling"
            ]):
                item.add_marker(skip_ci)
