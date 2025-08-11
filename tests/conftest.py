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

# Skip emotion tests in CI - they're performance-sensitive and flaky
def pytest_collection_modifyitems(config, items):
    """Skip emotion tests in CI environment."""
    if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true":
        skip_ci = pytest.mark.skip(reason="Skipped in CI - performance-sensitive test")
        for item in items:
            # Skip all emotion-related tests in CI
            if "emotion" in item.nodeid.lower():
                item.add_marker(skip_ci)
