"""
Advanced test suite for PromptTestRunner - comprehensive edge cases and performance scenarios.

This suite focuses on:
- Edge cases and boundary conditions
- Performance and scalability testing
- Error resilience and recovery
- Concurrent execution scenarios
- Memory and resource usage
- Real-world integration scenarios

Author: Test Generation Specialist for CRA-297
"""

import pytest
import time
import threading
import gc
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch

from services.common.prompt_test_runner import (
    PromptTestRunner,
    TestCase,
    TestSuite,
    TestRunnerError,
)


class TestPromptTestRunnerAdvancedEdgeCases:
    """Advanced edge case testing for PromptTestRunner."""

    @pytest.fixture
    def memory_limited_mock_model(self):
        """Mock model that simulates memory pressure."""
        mock_model = Mock()
        mock_model.name = "memory-test-model"
        mock_model.render.return_value = "Test output"
        return mock_model

    def test_extremely_large_input_data_handling(self, memory_limited_mock_model):
        """Test handling of extremely large input data (multiple GB)."""
        runner = PromptTestRunner(memory_limited_mock_model)

        # Create 100MB string
        large_data = "x" * (100 * 1024 * 1024)

        test_case = TestCase(
            name="large_input_test",
            input_data={"massive_data": large_data},
            expected_output="Test output",
            validation_rules=["exact_match"],
        )

        # Should handle large input without crashing
        result = runner.run_test_case(test_case)
        assert result.passed is True
        assert result.execution_time is not None

    def test_unicode_edge_cases_comprehensive(self, memory_limited_mock_model):
        """Test comprehensive unicode edge cases including emojis, RTL text, etc."""
        test_cases = [
            # Emoji combinations
            {"input": "👨‍👩‍👧‍👦", "expected": "👨‍👩‍👧‍👦"},
            # Right-to-left text
            {"input": "مرحبا بالعالم", "expected": "مرحبا بالعالم"},
            # Mixed scripts
            {"input": "Hello世界🌍नमस्ते", "expected": "Hello世界🌍नमस्ते"},
            # Zero-width characters
            {
                "input": "test\u200bzero\u200bwidth",
                "expected": "test\u200bzero\u200bwidth",
            },
            # Combining characters
            {"input": "e\u0301", "expected": "e\u0301"},  # é
            # Null bytes (should be handled safely)
            {"input": "test\x00null", "expected": "test\x00null"},
        ]

        runner = PromptTestRunner(memory_limited_mock_model)

        for i, case_data in enumerate(test_cases):
            memory_limited_mock_model.render.return_value = case_data["expected"]

            test_case = TestCase(
                name=f"unicode_test_{i}",
                input_data={"text": case_data["input"]},
                expected_output=case_data["expected"],
                validation_rules=["exact_match"],
            )

            result = runner.run_test_case(test_case)
            assert result.passed is True, f"Failed for case {i}: {case_data}"

    def test_malformed_validation_rules_handling(self, memory_limited_mock_model):
        """Test handling of malformed or invalid validation rules."""
        runner = PromptTestRunner(memory_limited_mock_model)
        memory_limited_mock_model.render.return_value = "Test output"

        malformed_rules = [
            "regex_match:",  # Missing pattern
            "length_range:invalid",  # Invalid range format
            "length_range:100,10",  # Invalid range (min > max)
            "max_execution_time:",  # Missing value
            "max_execution_time:invalid",  # Invalid time value
            "",  # Empty rule
            "unknown_rule:param",  # Unknown rule
        ]

        for rule in malformed_rules:
            test_case = TestCase(
                name=f"malformed_rule_test_{rule}",
                input_data={"input": "test"},
                expected_output="Test output",
                validation_rules=[rule],
            )

            with pytest.raises(TestRunnerError):
                runner.run_test_case(test_case)

    def test_circular_reference_in_input_data(self, memory_limited_mock_model):
        """Test handling of circular references in input data."""
        runner = PromptTestRunner(memory_limited_mock_model)
        memory_limited_mock_model.render.return_value = "Test output"

        # Create circular reference
        circular_dict = {"key": "value"}
        circular_dict["self"] = circular_dict

        test_case = TestCase(
            name="circular_reference_test",
            input_data={"circular": circular_dict},
            expected_output="Test output",
            validation_rules=["exact_match"],
        )

        # Should handle circular reference gracefully
        result = runner.run_test_case(test_case)
        assert result is not None

    def test_memory_leak_detection_during_execution(self, memory_limited_mock_model):
        """Test for memory leaks during repeated test execution."""
        runner = PromptTestRunner(memory_limited_mock_model)
        memory_limited_mock_model.render.return_value = "Test output"

        # Record initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Run many test cases
        for i in range(100):
            test_case = TestCase(
                name=f"memory_test_{i}",
                input_data={"iteration": i, "data": "x" * 1024},  # 1KB per test
                expected_output="Test output",
                validation_rules=["exact_match"],
            )

            result = runner.run_test_case(test_case)
            assert result.passed is True

            # Force garbage collection periodically
            if i % 20 == 0:
                gc.collect()

        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Allow some memory increase but it should be reasonable (< 50MB)
        assert memory_increase < 50 * 1024 * 1024, (
            f"Memory leak detected: {memory_increase} bytes"
        )

    def test_extremely_slow_model_timeout_handling(self, memory_limited_mock_model):
        """Test timeout handling for extremely slow model execution."""

        def slow_render(*args, **kwargs):
            time.sleep(5)  # 5 second delay
            return "Slow output"

        memory_limited_mock_model.render.side_effect = slow_render

        runner = PromptTestRunner(memory_limited_mock_model)
        test_case = TestCase(
            name="timeout_test",
            input_data={"input": "test"},
            expected_output="Slow output",
            validation_rules=["exact_match", "max_execution_time:1.0"],  # 1 second max
        )

        result = runner.run_test_case(test_case)
        assert result.passed is False
        assert "execution_time" in result.error
        assert result.execution_time > 1.0

    def test_model_exception_during_rendering_comprehensive(
        self, memory_limited_mock_model
    ):
        """Test comprehensive exception handling during model rendering."""
        exception_types = [
            ValueError("Invalid value"),
            TypeError("Type mismatch"),
            KeyError("Missing key"),
            AttributeError("Missing attribute"),
            RuntimeError("Runtime error"),
            MemoryError("Out of memory"),
            RecursionError("Maximum recursion depth exceeded"),
        ]

        runner = PromptTestRunner(memory_limited_mock_model)

        for i, exception in enumerate(exception_types):
            memory_limited_mock_model.render.side_effect = exception

            test_case = TestCase(
                name=f"exception_test_{i}",
                input_data={"input": "test"},
                expected_output="Test output",
                validation_rules=["exact_match"],
            )

            result = runner.run_test_case(test_case)
            assert result.passed is False
            assert result.error is not None
            assert str(exception) in result.error


class TestPromptTestRunnerConcurrencyAndPerformance:
    """Test concurrent execution and performance characteristics."""

    @pytest.fixture
    def thread_safe_mock_model(self):
        """Thread-safe mock model for concurrent testing."""
        mock_model = Mock()
        mock_model.name = "thread-safe-model"
        mock_model.render.return_value = "Thread safe output"
        return mock_model

    def test_high_concurrency_execution(self, thread_safe_mock_model):
        """Test high-concurrency execution with many threads."""
        num_threads = 50
        tests_per_thread = 10
        results = []
        errors = []

        def run_tests_in_thread(thread_id: int):
            try:
                runner = PromptTestRunner(thread_safe_mock_model)
                thread_results = []

                for i in range(tests_per_thread):
                    test_case = TestCase(
                        name=f"concurrent_t{thread_id}_test_{i}",
                        input_data={"thread_id": thread_id, "test_id": i},
                        expected_output="Thread safe output",
                        validation_rules=["exact_match"],
                    )

                    result = runner.run_test_case(test_case)
                    thread_results.append(result)

                return thread_results
            except Exception as e:
                errors.append(str(e))
                return []

        # Execute in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(run_tests_in_thread, i) for i in range(num_threads)
            ]

            for future in as_completed(futures):
                thread_results = future.result()
                results.extend(thread_results)

        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == num_threads * tests_per_thread
        assert all(result.passed for result in results)

    def test_performance_under_load(self, thread_safe_mock_model):
        """Test performance characteristics under high load."""
        runner = PromptTestRunner(thread_safe_mock_model)

        # Create a large test suite
        large_test_suite = TestSuite(
            name="performance_load_test",
            test_cases=[
                TestCase(
                    name=f"load_test_{i}",
                    input_data={"iteration": i, "data": f"test_data_{i}"},
                    expected_output="Thread safe output",
                    validation_rules=["exact_match"],
                )
                for i in range(1000)  # 1000 test cases
            ],
        )

        runner.test_suite = large_test_suite

        # Measure execution time
        start_time = time.time()
        results = runner.run_test_suite()
        execution_time = time.time() - start_time

        # Verify results
        assert len(results) == 1000
        assert all(result.passed for result in results)

        # Performance requirements
        assert execution_time < 30.0  # Should complete within 30 seconds

        # Calculate throughput
        throughput = len(results) / execution_time
        assert throughput > 30, f"Low throughput: {throughput} tests/second"

    def test_memory_usage_scaling(self, thread_safe_mock_model):
        """Test memory usage scaling with increasing load."""
        runner = PromptTestRunner(thread_safe_mock_model)
        process = psutil.Process()

        memory_measurements = []
        test_suite_sizes = [10, 50, 100, 500, 1000]

        for size in test_suite_sizes:
            # Force garbage collection before measurement
            gc.collect()
            initial_memory = process.memory_info().rss

            # Create test suite of specified size
            test_suite = TestSuite(
                name=f"memory_scaling_test_{size}",
                test_cases=[
                    TestCase(
                        name=f"memory_test_{i}",
                        input_data={"iteration": i},
                        expected_output="Thread safe output",
                        validation_rules=["exact_match"],
                    )
                    for i in range(size)
                ],
            )

            runner.test_suite = test_suite
            results = runner.run_test_suite()

            final_memory = process.memory_info().rss
            memory_used = final_memory - initial_memory
            memory_measurements.append((size, memory_used))

            assert len(results) == size
            assert all(result.passed for result in results)

        # Memory usage should scale reasonably (not exponentially)
        # Check that memory usage per test case is consistent
        memory_per_test = [
            mem / size for size, mem in memory_measurements[1:]
        ]  # Skip first measurement

        # Memory per test should be consistent (within 2x variation)
        max_memory_per_test = max(memory_per_test)
        min_memory_per_test = min(memory_per_test)
        memory_ratio = (
            max_memory_per_test / min_memory_per_test if min_memory_per_test > 0 else 1
        )

        assert memory_ratio < 2.0, (
            f"Memory usage scaling issue: {memory_ratio}x variation"
        )

    def test_resource_cleanup_after_execution(self, thread_safe_mock_model):
        """Test proper resource cleanup after test execution."""
        runner = PromptTestRunner(thread_safe_mock_model)

        # Record initial resource usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        initial_threads = threading.active_count()

        # Run many test suites
        for suite_id in range(10):
            test_suite = TestSuite(
                name=f"cleanup_test_suite_{suite_id}",
                test_cases=[
                    TestCase(
                        name=f"cleanup_test_{i}",
                        input_data={"data": "x" * 10240},  # 10KB per test
                        expected_output="Thread safe output",
                        validation_rules=["exact_match"],
                    )
                    for i in range(100)
                ],
            )

            runner.test_suite = test_suite
            results = runner.run_test_suite()
            assert len(results) == 100

            # Force cleanup
            del results
            del test_suite
            gc.collect()

        # Check final resource usage
        final_memory = process.memory_info().rss
        final_threads = threading.active_count()

        memory_increase = final_memory - initial_memory
        thread_increase = final_threads - initial_threads

        # Allow some memory increase but it should be reasonable
        assert memory_increase < 100 * 1024 * 1024, (
            f"Excessive memory usage: {memory_increase} bytes"
        )
        assert thread_increase <= 2, (
            f"Thread leak detected: {thread_increase} extra threads"
        )


class TestPromptTestRunnerRealWorldScenarios:
    """Test real-world integration scenarios and use cases."""

    @pytest.fixture
    def realistic_prompt_model(self):
        """Mock model that simulates realistic prompt behavior."""
        mock_model = Mock()
        mock_model.name = "realistic-llm-model"
        mock_model.version = "v2.1.0"
        mock_model.template = "Process this request: {user_input}"

        def realistic_render(**kwargs):
            user_input = kwargs.get("user_input", "")

            # Simulate different response patterns
            if "error" in user_input.lower():
                raise ValueError("Simulated processing error")
            elif "slow" in user_input.lower():
                time.sleep(0.5)  # Simulate slow processing
                return f"Slowly processed: {user_input}"
            elif "empty" in user_input.lower():
                return ""
            elif len(user_input) > 1000:
                return f"Large input processed: {len(user_input)} characters"
            else:
                return f"Processed: {user_input}"

        mock_model.render.side_effect = realistic_render
        return mock_model

    def test_production_like_test_suite_execution(self, realistic_prompt_model):
        """Test execution of a production-like comprehensive test suite."""
        runner = PromptTestRunner(realistic_prompt_model)

        # Create comprehensive test suite mimicking production scenarios
        production_test_cases = [
            # Normal cases
            TestCase(
                name="greeting_generation",
                input_data={"user_input": "Hello, how are you?"},
                expected_output="Processed: Hello, how are you?",
                validation_rules=["exact_match", "max_execution_time:2.0"],
            ),
            # Edge cases
            TestCase(
                name="empty_input_handling",
                input_data={"user_input": "empty request"},
                expected_output="",
                validation_rules=["handles_empty_input"],
            ),
            # Performance cases
            TestCase(
                name="large_input_processing",
                input_data={"user_input": "x" * 2000},
                expected_output="Large input processed: 2000 characters",
                validation_rules=[
                    "contains:Large input processed",
                    "max_execution_time:3.0",
                ],
            ),
            # Slow processing cases
            TestCase(
                name="slow_processing_timeout",
                input_data={"user_input": "slow request"},
                expected_output="Slowly processed: slow request",
                validation_rules=[
                    "contains:Slowly processed",
                    "max_execution_time:1.0",
                ],  # Will fail due to timeout
            ),
            # Error cases
            TestCase(
                name="error_handling",
                input_data={"user_input": "trigger error"},
                expected_output="Error handled",
                validation_rules=["exact_match"],  # Will fail due to exception
            ),
        ]

        test_suite = TestSuite(
            name="production_integration_suite", test_cases=production_test_cases
        )

        runner.test_suite = test_suite
        results = runner.run_test_suite()

        # Analyze results
        assert len(results) == 5

        # Check specific results
        passed_tests = [r for r in results if r.passed]
        failed_tests = [r for r in results if not r.passed]

        # Should have some passes and some expected failures
        assert len(passed_tests) >= 2  # Normal cases should pass
        assert len(failed_tests) >= 2  # Timeout and error cases should fail

        # Verify error messages are informative
        for failed_test in failed_tests:
            assert failed_test.error is not None
            assert len(failed_test.error) > 10  # Descriptive error message

    def test_integration_with_model_registry_workflow(self, realistic_prompt_model):
        """Test integration with model registry deployment workflow."""
        # Simulate model registry integration
        with patch("services.common.prompt_model_registry.get_mlflow_client"):
            runner = PromptTestRunner(realistic_prompt_model)

            # Pre-deployment validation suite
            pre_deployment_suite = TestSuite(
                name="pre_deployment_validation",
                test_cases=[
                    TestCase(
                        name="basic_functionality_check",
                        input_data={"user_input": "basic test"},
                        expected_output="Processed: basic test",
                        validation_rules=["exact_match"],
                    ),
                    TestCase(
                        name="performance_benchmark",
                        input_data={"user_input": "performance test"},
                        expected_output="Processed: performance test",
                        validation_rules=["exact_match", "max_execution_time:0.5"],
                    ),
                    TestCase(
                        name="safety_check",
                        input_data={"user_input": "safety validation"},
                        expected_output="Processed: safety validation",
                        validation_rules=["contains:Processed", "length_range:10,100"],
                    ),
                ],
            )

            runner.test_suite = pre_deployment_suite
            results = runner.run_test_suite()

            # Generate deployment report
            summary = runner.generate_summary_report(results)
            detailed_report = runner.generate_detailed_report(results)
            json_export = runner.export_results_to_json(results)

            # Verify deployment readiness
            assert (
                summary["success_rate"] == 1.0
            )  # All tests should pass for deployment
            assert detailed_report["summary"]["total_tests"] == 3
            assert "pre_deployment_validation" in json_export

            # Verify performance requirements
            max_execution_time = max(result.execution_time for result in results)
            assert max_execution_time < 1.0  # Performance requirement for deployment

    def test_continuous_integration_pipeline_simulation(self, realistic_prompt_model):
        """Test simulation of continuous integration pipeline execution."""
        runner = PromptTestRunner(realistic_prompt_model)

        # Simulate multiple test runs as in CI pipeline
        ci_test_runs = []

        for run_id in range(5):  # 5 CI runs
            test_suite = TestSuite(
                name=f"ci_run_{run_id}",
                test_cases=[
                    TestCase(
                        name=f"ci_test_{i}",
                        input_data={"user_input": f"CI test {run_id}-{i}"},
                        expected_output=f"Processed: CI test {run_id}-{i}",
                        validation_rules=["exact_match", "max_execution_time:1.0"],
                    )
                    for i in range(10)  # 10 tests per run
                ],
            )

            runner.test_suite = test_suite

            # Measure CI run performance
            start_time = time.time()
            results = runner.run_test_suite()
            ci_duration = time.time() - start_time

            ci_run_data = {
                "run_id": run_id,
                "results": results,
                "duration": ci_duration,
                "success_rate": sum(1 for r in results if r.passed) / len(results),
            }

            ci_test_runs.append(ci_run_data)

        # Analyze CI pipeline performance
        total_tests = sum(len(run["results"]) for run in ci_test_runs)
        average_duration = sum(run["duration"] for run in ci_test_runs) / len(
            ci_test_runs
        )
        overall_success_rate = sum(run["success_rate"] for run in ci_test_runs) / len(
            ci_test_runs
        )

        # CI pipeline requirements
        assert total_tests == 50  # 5 runs × 10 tests
        assert average_duration < 5.0  # Each CI run should be fast
        assert overall_success_rate >= 0.95  # High reliability requirement

        # Verify consistency across runs
        success_rates = [run["success_rate"] for run in ci_test_runs]
        success_rate_variance = max(success_rates) - min(success_rates)
        assert success_rate_variance < 0.1  # Consistent performance across runs


class TestPromptTestRunnerFailureInjection:
    """Test failure injection and resilience scenarios."""

    @pytest.fixture
    def failure_injection_model(self):
        """Mock model that can inject various failure modes."""
        mock_model = Mock()
        mock_model.name = "failure-injection-model"

        def failure_render(**kwargs):
            failure_mode = kwargs.get("failure_mode", "none")

            if failure_mode == "timeout":
                time.sleep(10)  # Long timeout
                return "Timeout test"
            elif failure_mode == "memory_error":
                raise MemoryError("Simulated out of memory")
            elif failure_mode == "network_error":
                raise ConnectionError("Simulated network failure")
            elif failure_mode == "intermittent":
                import random

                if random.random() < 0.3:  # 30% failure rate
                    raise RuntimeError("Intermittent failure")
                return "Success after retry"
            elif failure_mode == "data_corruption":
                return "Corrupted\x00\xff\xfedata"
            else:
                return f"Normal output for {kwargs.get('input', 'unknown')}"

        mock_model.render.side_effect = failure_render
        return mock_model

    def test_network_failure_resilience(self, failure_injection_model):
        """Test resilience to network failures during test execution."""
        runner = PromptTestRunner(failure_injection_model)

        test_case = TestCase(
            name="network_failure_test",
            input_data={"failure_mode": "network_error", "input": "test"},
            expected_output="Normal output",
            validation_rules=["exact_match"],
        )

        result = runner.run_test_case(test_case)

        assert result.passed is False
        assert "network failure" in result.error.lower()
        assert result.execution_time is not None

    def test_memory_pressure_handling(self, failure_injection_model):
        """Test handling of memory pressure and out-of-memory conditions."""
        runner = PromptTestRunner(failure_injection_model)

        test_case = TestCase(
            name="memory_pressure_test",
            input_data={"failure_mode": "memory_error", "input": "test"},
            expected_output="Normal output",
            validation_rules=["exact_match"],
        )

        result = runner.run_test_case(test_case)

        assert result.passed is False
        assert "memory" in result.error.lower()

    def test_intermittent_failure_handling(self, failure_injection_model):
        """Test handling of intermittent failures with retry logic."""
        runner = PromptTestRunner(failure_injection_model)

        # Run multiple tests to catch intermittent failures
        results = []
        for i in range(20):
            test_case = TestCase(
                name=f"intermittent_test_{i}",
                input_data={"failure_mode": "intermittent", "input": f"test_{i}"},
                expected_output="Success after retry",
                validation_rules=["exact_match"],
            )

            result = runner.run_test_case(test_case)
            results.append(result)

        # Should have mix of successes and failures due to intermittent nature
        passed_count = sum(1 for r in results if r.passed)
        failed_count = len(results) - passed_count

        assert passed_count > 0  # Some should succeed
        assert failed_count > 0  # Some should fail (intermittent)
        assert failed_count < len(results) * 0.5  # But not majority

    def test_data_corruption_detection(self, failure_injection_model):
        """Test detection of data corruption in model outputs."""
        runner = PromptTestRunner(failure_injection_model)

        test_case = TestCase(
            name="data_corruption_test",
            input_data={"failure_mode": "data_corruption", "input": "test"},
            expected_output="Normal clean output",
            validation_rules=["exact_match"],
        )

        result = runner.run_test_case(test_case)

        assert result.passed is False
        assert result.actual_output is not None
        # Should detect that output contains corruption
        assert "\x00" in result.actual_output or "\xff" in result.actual_output

    def test_cascading_failure_isolation(self, failure_injection_model):
        """Test that failures in one test don't cascade to others."""
        runner = PromptTestRunner(failure_injection_model)

        # Mix of failing and passing tests
        test_cases = [
            TestCase(
                name="normal_test_1",
                input_data={"failure_mode": "none", "input": "test1"},
                expected_output="Normal output for test1",
                validation_rules=["exact_match"],
            ),
            TestCase(
                name="failing_test",
                input_data={"failure_mode": "memory_error", "input": "test2"},
                expected_output="Normal output for test2",
                validation_rules=["exact_match"],
            ),
            TestCase(
                name="normal_test_2",
                input_data={"failure_mode": "none", "input": "test3"},
                expected_output="Normal output for test3",
                validation_rules=["exact_match"],
            ),
        ]

        test_suite = TestSuite(name="isolation_test", test_cases=test_cases)
        runner.test_suite = test_suite

        results = runner.run_test_suite()

        # Verify isolation - normal tests should pass despite failing test
        assert len(results) == 3
        assert results[0].passed is True  # normal_test_1
        assert results[1].passed is False  # failing_test
        assert results[2].passed is True  # normal_test_2


@pytest.mark.performance
class TestPromptTestRunnerPerformanceRequirements:
    """Test specific performance requirements and SLAs."""

    def test_single_test_execution_latency(self):
        """Test that single test execution meets latency requirements."""
        mock_model = Mock()
        mock_model.render.return_value = "Fast output"

        runner = PromptTestRunner(mock_model)
        test_case = TestCase(
            name="latency_test",
            input_data={"input": "test"},
            expected_output="Fast output",
            validation_rules=["exact_match"],
        )

        # Execute multiple times to get average
        execution_times = []
        for _ in range(100):
            start_time = time.time()
            result = runner.run_test_case(test_case)
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            assert result.passed is True

        # Performance requirements
        average_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)

        assert average_time < 0.1  # Average execution under 100ms
        assert max_time < 0.5  # Maximum execution under 500ms

    def test_test_suite_throughput_requirements(self):
        """Test test suite throughput requirements."""
        mock_model = Mock()
        mock_model.render.return_value = "Throughput test output"

        runner = PromptTestRunner(mock_model)

        # Large test suite for throughput testing
        large_suite = TestSuite(
            name="throughput_test",
            test_cases=[
                TestCase(
                    name=f"throughput_test_{i}",
                    input_data={"iteration": i},
                    expected_output="Throughput test output",
                    validation_rules=["exact_match"],
                )
                for i in range(500)
            ],
        )

        runner.test_suite = large_suite

        start_time = time.time()
        results = runner.run_test_suite()
        execution_time = time.time() - start_time

        # Throughput requirements
        throughput = len(results) / execution_time

        assert len(results) == 500
        assert all(r.passed for r in results)
        assert throughput > 50  # Minimum 50 tests per second
        assert execution_time < 15  # Complete 500 tests in under 15 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
