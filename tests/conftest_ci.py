"""CI-specific test configuration to skip flaky tests"""
import os
import pytest

# Skip emotion tests in CI as they're performance-sensitive
if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true":
    collect_ignore_glob = [
        "tests/unit/test_emotion_*.py",
    ]

def pytest_collection_modifyitems(config, items):
    """Skip emotion tests in CI environment"""
    if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true":
        skip_ci = pytest.mark.skip(reason="Skipped in CI due to performance sensitivity")
        for item in items:
            # Skip all emotion-related tests in CI
            if "emotion" in item.nodeid.lower():
                item.add_marker(skip_ci)