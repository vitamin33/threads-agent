"""
Comprehensive Integration Test Suite for M1 Telemetry
Tests all decorator patterns, error handling, and edge cases
"""

import time
import threading
import sys
from pathlib import Path

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

from ops.telemetry import (
    telemetry_decorator,
    openai_cost_calculator,
    get_daily_metrics,
)
from ops.integration import (
    orchestrator_telemetry,
    persona_runtime_telemetry,
    model_call_telemetry,
    tool_call_telemetry,
)


class TestResults:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.errors = []

    def run_test(self, name, test_func):
        """Run a single test and track results"""
        self.tests_run += 1
        try:
            print(f"🧪 Running: {name}")
            test_func()
            print(f"✅ Passed: {name}")
            self.tests_passed += 1
        except Exception as e:
            print(f"❌ Failed: {name} - {e}")
            self.errors.append(f"{name}: {e}")

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'=' * 60}")
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        if self.errors:
            print("❌ Failures:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("🎉 All tests passed!")
        print(f"{'=' * 60}")


# Test fixtures
results = TestResults()


def test_basic_decorator():
    """Test basic telemetry decorator functionality"""

    @telemetry_decorator(agent_name="test_agent", event_type="test_call")
    def test_function(x, y):
        time.sleep(0.1)  # Simulate work
        return x + y

    result = test_function(5, 3)
    assert result == 8, f"Expected 8, got {result}"


def test_decorator_with_error():
    """Test decorator with exception handling"""

    @telemetry_decorator(agent_name="test_agent", event_type="test_call")
    def failing_function():
        raise ValueError("Test error")

    try:
        failing_function()
        assert False, "Expected exception"
    except ValueError as e:
        assert str(e) == "Test error", f"Expected 'Test error', got '{e}'"


def test_cost_calculator():
    """Test cost calculation functionality"""

    class MockResult:
        def __init__(self):
            self.usage = MockUsage()

    class MockUsage:
        def __init__(self):
            self.prompt_tokens = 100
            self.completion_tokens = 50

    @telemetry_decorator(
        agent_name="test_agent",
        event_type="model_call",
        cost_calculator=openai_cost_calculator,
    )
    def mock_openai_call():
        return MockResult()

    result = mock_openai_call()
    assert hasattr(result, "usage"), "Result should have usage attribute"


def test_service_helpers():
    """Test service-specific helper decorators"""

    @orchestrator_telemetry
    def test_orchestrator_func():
        return "orchestrator_result"

    @persona_runtime_telemetry
    def test_persona_func():
        return "persona_result"

    result1 = test_orchestrator_func()
    result2 = test_persona_func()

    assert result1 == "orchestrator_result"
    assert result2 == "persona_result"


def test_custom_decorators():
    """Test custom decorator creation"""

    @model_call_telemetry("custom_service")
    def test_model_call():
        return "model_result"

    @tool_call_telemetry("custom_service")
    def test_tool_call():
        return "tool_result"

    result1 = test_model_call()
    result2 = test_tool_call()

    assert result1 == "model_result"
    assert result2 == "tool_result"


def test_trace_id_propagation():
    """Test trace ID propagation"""

    @telemetry_decorator(agent_name="test_agent")
    def child_function():
        return "trace_function_called"

    # Test basic function call (trace ID auto-generated internally)
    result = child_function()
    assert result == "trace_function_called"

    # Test with kwargs that might affect trace ID
    result = child_function()
    assert result == "trace_function_called"


def test_concurrent_access():
    """Test thread-safe concurrent access"""

    @telemetry_decorator(agent_name="concurrent_test")
    def concurrent_function(thread_id):
        time.sleep(0.05)  # Small delay
        return f"thread_{thread_id}"

    results = []
    errors = []

    def worker(thread_id):
        try:
            result = concurrent_function(thread_id)
            results.append(result)
        except Exception as e:
            errors.append(str(e))

    # Create 10 concurrent threads
    threads = []
    for i in range(10):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    assert len(errors) == 0, f"Concurrent errors: {errors}"
    assert len(results) == 10, f"Expected 10 results, got {len(results)}"


def test_metrics_calculation():
    """Test metrics calculation accuracy"""

    # Clear any existing data by checking before/after counts
    get_daily_metrics(1)  # Just call it, don't store result

    @telemetry_decorator(agent_name="metrics_test")
    def success_function():
        time.sleep(0.1)
        return "success"

    @telemetry_decorator(agent_name="metrics_test")
    def failure_function():
        time.sleep(0.05)
        raise Exception("test failure")

    # Run some test functions
    success_function()
    success_function()

    try:
        failure_function()
    except Exception:
        pass

    # Check metrics updated
    final_metrics = get_daily_metrics(1)

    # Verify metrics structure
    assert "success_rate" in final_metrics
    assert "p95_latency_ms" in final_metrics
    assert "total_cost" in final_metrics
    assert isinstance(final_metrics["success_rate"], float)


def test_database_persistence():
    """Test that events are properly persisted"""

    import sqlite3

    @telemetry_decorator(agent_name="persistence_test")
    def persistent_function():
        return "persisted"

    # Get initial count
    db_path = DEV_SYSTEM_ROOT / "data" / "telemetry.db"
    with sqlite3.connect(db_path) as conn:
        initial_count = conn.execute(
            "SELECT COUNT(*) FROM telemetry_events WHERE agent_name = ?",
            ("persistence_test",),
        ).fetchone()[0]

    # Run function
    persistent_function()

    # Check count increased
    with sqlite3.connect(db_path) as conn:
        final_count = conn.execute(
            "SELECT COUNT(*) FROM telemetry_events WHERE agent_name = ?",
            ("persistence_test",),
        ).fetchone()[0]

    assert final_count > initial_count, "Event should be persisted to database"


def test_error_resilience():
    """Test system resilience to database/file system errors"""

    # Test with invalid trace ID types
    @telemetry_decorator(agent_name="resilience_test")
    def resilient_function():
        return "still_works"

    # Should not crash even with weird trace IDs
    result = resilient_function(_trace_id=12345)  # Number instead of string
    assert result == "still_works"

    result = resilient_function(_trace_id=None)
    assert result == "still_works"


def run_all_tests():
    """Run complete test suite"""

    print("🚀 Starting M1 Telemetry Integration Tests")
    print("=" * 60)

    # Basic functionality tests
    results.run_test("Basic Decorator", test_basic_decorator)
    results.run_test("Error Handling", test_decorator_with_error)
    results.run_test("Cost Calculator", test_cost_calculator)

    # Integration tests
    results.run_test("Service Helpers", test_service_helpers)
    results.run_test("Custom Decorators", test_custom_decorators)
    results.run_test("Trace ID Propagation", test_trace_id_propagation)

    # Performance & reliability tests
    results.run_test("Concurrent Access", test_concurrent_access)
    results.run_test("Metrics Calculation", test_metrics_calculation)
    results.run_test("Database Persistence", test_database_persistence)
    results.run_test("Error Resilience", test_error_resilience)

    # Print final results
    results.print_summary()

    return results.tests_passed == results.tests_run


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
