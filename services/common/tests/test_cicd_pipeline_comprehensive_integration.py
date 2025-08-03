"""
Comprehensive integration test suite for complete CI/CD Pipeline.

This suite focuses on:
- End-to-end pipeline workflows with all components
- Complex failure scenarios and recovery patterns
- Performance requirements across the entire pipeline
- Real-world production scenarios and edge cases
- Cross-component communication and data flow
- Pipeline reliability and resilience testing

Author: Test Generation Specialist for CRA-297
"""

import pytest
import time
import numpy as np
from unittest.mock import Mock
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from services.common.prompt_test_runner import (
    PromptTestRunner,
    TestCase,
    TestSuite,
)
from services.common.performance_regression_detector import (
    PerformanceRegressionDetector,
    PerformanceData,
    SignificanceLevel,
)
from services.common.gradual_rollout_manager import GradualRolloutManager, RolloutStage
from services.common.rollback_controller import RollbackController, RollbackTrigger


class TestComprehensiveCICDPipelineIntegration:
    """Comprehensive integration tests for the complete CI/CD pipeline."""

    @pytest.fixture
    def production_pipeline_components(self):
        """Set up production-like pipeline components."""
        # Create realistic prompt model mock
        mock_prompt_model = Mock()
        mock_prompt_model.name = "production_llm_model"
        mock_prompt_model.version = "v2.1.0"
        mock_prompt_model.template = "Process: {input} -> Output: {expected_format}"

        def realistic_render(**kwargs):
            input_text = kwargs.get("input", "")
            format_type = kwargs.get("expected_format", "json")

            # Simulate realistic processing delays
            processing_time = len(input_text) * 0.001  # 1ms per character
            time.sleep(processing_time)

            if "error" in input_text.lower():
                raise ValueError("Processing error in prompt model")
            elif len(input_text) > 1000:
                return (
                    f"Large input processed: {len(input_text)} chars in {format_type}"
                )
            else:
                return f"Processed '{input_text}' as {format_type}"

        mock_prompt_model.render.side_effect = realistic_render

        # Create realistic model registry mock
        mock_model_registry = Mock()
        mock_model_registry.current_model = "v2.1.0"
        mock_model_registry.fallback_model = "v2.0.5"

        def realistic_rollback(target_model):
            # Simulate rollback time
            rollback_delay = np.random.uniform(5, 15)  # 5-15 seconds
            time.sleep(rollback_delay)
            return Mock(success=True, duration=rollback_delay)

        mock_model_registry.rollback_to_model.side_effect = realistic_rollback

        # Create pipeline components
        test_runner = PromptTestRunner(mock_prompt_model)
        regression_detector = PerformanceRegressionDetector(
            significance_level=SignificanceLevel.ALPHA_05,
            minimum_samples=5,
            baseline_window_days=7,
        )
        rollout_manager = GradualRolloutManager(regression_detector)
        rollback_controller = RollbackController(
            regression_detector, mock_model_registry
        )

        return {
            "test_runner": test_runner,
            "regression_detector": regression_detector,
            "rollout_manager": rollout_manager,
            "rollback_controller": rollback_controller,
            "mock_model_registry": mock_model_registry,
            "mock_prompt_model": mock_prompt_model,
        }

    def test_complete_successful_deployment_pipeline(
        self, production_pipeline_components
    ):
        """Test complete successful deployment pipeline from testing to production."""
        components = production_pipeline_components
        test_runner = components["test_runner"]
        rollout_manager = components["rollout_manager"]
        rollback_controller = components["rollback_controller"]

        pipeline_start_time = time.time()

        # Phase 1: Pre-deployment Testing
        print("\\n=== Phase 1: Pre-deployment Testing ===")

        comprehensive_test_suite = TestSuite(
            name="Pre-deployment Validation Suite",
            test_cases=[
                TestCase(
                    name="basic_functionality",
                    input_data={
                        "input": "test basic function",
                        "expected_format": "json",
                    },
                    expected_output="Processed 'test basic function' as json",
                    validation_rules=["exact_match", "max_execution_time:1.0"],
                ),
                TestCase(
                    name="performance_benchmark",
                    input_data={"input": "performance test", "expected_format": "xml"},
                    expected_output="Processed 'performance test' as xml",
                    validation_rules=["exact_match", "max_execution_time:0.5"],
                ),
                TestCase(
                    name="large_input_handling",
                    input_data={"input": "x" * 500, "expected_format": "json"},
                    expected_output="Large input processed: 500 chars in json",
                    validation_rules=[
                        "contains:Large input processed",
                        "max_execution_time:2.0",
                    ],
                ),
                TestCase(
                    name="format_flexibility",
                    input_data={"input": "format test", "expected_format": "yaml"},
                    expected_output="Processed 'format test' as yaml",
                    validation_rules=["contains:format test", "contains:yaml"],
                ),
            ],
        )

        test_runner.test_suite = comprehensive_test_suite
        test_results = test_runner.run_test_suite()

        # Verify all tests pass
        assert len(test_results) == 4
        assert all(result.passed for result in test_results), (
            "Pre-deployment tests must pass"
        )

        test_summary = test_runner.generate_summary_report(test_results)
        assert test_summary["success_rate"] == 1.0

        print(
            f"Pre-deployment tests completed: {test_summary['success_rate'] * 100:.1f}% success rate"
        )

        # Phase 2: Start Gradual Rollout
        print("\\n=== Phase 2: Gradual Rollout Initiation ===")

        rollout_result = rollout_manager.start_rollout("model_v2.1.0")
        assert rollout_result.success is True
        assert rollout_manager.current_stage == RolloutStage.CANARY_10

        # Start rollback monitoring
        monitor_result = rollback_controller.start_monitoring(
            "model_v2.1.0", "model_v2.0.5"
        )
        assert monitor_result.success is True

        print(f"Rollout started at stage: {rollout_manager.current_stage.stage_name}")

        # Phase 3: Progressive Rollout with Health Monitoring
        print("\\n=== Phase 3: Progressive Rollout ===")

        # Generate realistic performance data showing stable/improving performance
        def generate_performance_data(stage_name: str, is_improving: bool = True):
            base_accuracy = 0.85
            base_latency = 150  # ms

            # Historical data (last 7 days)
            historical_accuracy = []
            historical_latency = []

            for hour in range(168):  # 7 days * 24 hours
                # Add daily and weekly patterns
                hour_of_day = hour % 24
                day_of_week = (hour // 24) % 7

                # Business hours have different performance characteristics
                business_factor = (
                    1.1 if 9 <= hour_of_day <= 17 and day_of_week < 5 else 1.0
                )

                accuracy = base_accuracy + np.random.normal(0, 0.02) * business_factor
                latency = base_latency * business_factor + np.random.exponential(10)

                historical_accuracy.append(
                    PerformanceData(
                        timestamp=datetime.now() - timedelta(hours=168 - hour),
                        metric_name="accuracy",
                        value=max(0, min(1, accuracy)),
                        metadata={"stage": "baseline", "hour_of_day": hour_of_day},
                    )
                )

                historical_latency.append(
                    PerformanceData(
                        timestamp=datetime.now() - timedelta(hours=168 - hour),
                        metric_name="response_latency_ms",
                        value=max(0, latency),
                        metadata={"stage": "baseline", "hour_of_day": hour_of_day},
                    )
                )

            # Current data (last hour)
            current_accuracy = []
            current_latency = []

            improvement_factor = 1.02 if is_improving else 0.98

            for minute in range(60):
                accuracy = base_accuracy * improvement_factor + np.random.normal(
                    0, 0.01
                )
                latency = base_latency / improvement_factor + np.random.exponential(5)

                current_accuracy.append(
                    PerformanceData(
                        timestamp=datetime.now() - timedelta(minutes=60 - minute),
                        metric_name="accuracy",
                        value=max(0, min(1, accuracy)),
                        metadata={"stage": stage_name, "minute": minute},
                    )
                )

                current_latency.append(
                    PerformanceData(
                        timestamp=datetime.now() - timedelta(minutes=60 - minute),
                        metric_name="response_latency_ms",
                        value=max(0, latency),
                        metadata={"stage": stage_name, "minute": minute},
                    )
                )

            return {
                "accuracy": {
                    "historical": historical_accuracy,
                    "current": current_accuracy,
                },
                "latency": {
                    "historical": historical_latency,
                    "current": current_latency,
                },
            }

        # Progress through rollout stages
        expected_stages = [
            RolloutStage.CANARY_25,
            RolloutStage.CANARY_50,
            RolloutStage.FULL_ROLLOUT,
        ]

        for target_stage in expected_stages:
            stage_start_time = time.time()

            # Generate performance data for this stage
            perf_data = generate_performance_data(
                target_stage.stage_name, is_improving=True
            )

            # Check health for both accuracy and latency
            accuracy_health = rollback_controller.check_health(
                perf_data["accuracy"]["historical"], perf_data["accuracy"]["current"]
            )

            latency_health = rollback_controller.check_health(
                perf_data["latency"]["historical"], perf_data["latency"]["current"]
            )

            assert accuracy_health.is_healthy is True, (
                f"Accuracy health check failed at {target_stage.stage_name}"
            )
            assert latency_health.is_healthy is True, (
                f"Latency health check failed at {target_stage.stage_name}"
            )

            # Check for automatic rollback triggers (should be None for healthy metrics)
            auto_rollback_accuracy = (
                rollback_controller.trigger_automatic_rollback_if_needed(
                    perf_data["accuracy"]["historical"],
                    perf_data["accuracy"]["current"],
                )
            )

            auto_rollback_latency = (
                rollback_controller.trigger_automatic_rollback_if_needed(
                    perf_data["latency"]["historical"], perf_data["latency"]["current"]
                )
            )

            assert auto_rollback_accuracy is None, (
                "No rollback should be triggered for healthy accuracy"
            )
            assert auto_rollback_latency is None, (
                "No rollback should be triggered for healthy latency"
            )

            # Advance rollout stage
            advance_result = rollout_manager.advance_stage(
                perf_data["accuracy"]["historical"], perf_data["accuracy"]["current"]
            )

            assert advance_result.success is True, (
                f"Failed to advance to {target_stage.stage_name}"
            )
            assert rollout_manager.current_stage == target_stage

            stage_duration = time.time() - stage_start_time
            print(
                f"Advanced to {target_stage.stage_name} ({target_stage.traffic_percentage}%) in {stage_duration:.2f}s"
            )

        # Phase 4: Deployment Completion Verification
        print("\\n=== Phase 4: Deployment Completion ===")

        final_status = rollout_manager.get_rollout_status()
        assert final_status.current_stage == RolloutStage.FULL_ROLLOUT
        assert final_status.is_active is False  # Rollout completed

        rollback_status = rollback_controller.get_rollback_status()
        assert rollback_status.rollback_count == 0  # No rollbacks occurred

        pipeline_duration = time.time() - pipeline_start_time
        print(f"Complete pipeline duration: {pipeline_duration:.2f}s")

        # Pipeline performance requirements
        assert pipeline_duration < 120.0, (
            f"Pipeline took too long: {pipeline_duration:.2f}s"
        )

    def test_pipeline_with_cascading_failures_and_recovery(
        self, production_pipeline_components
    ):
        """Test pipeline behavior with cascading failures and recovery mechanisms."""
        components = production_pipeline_components
        test_runner = components["test_runner"]
        rollout_manager = components["rollout_manager"]
        rollback_controller = components["rollback_controller"]
        mock_model = components["mock_prompt_model"]

        print("\\n=== Testing Cascading Failure Scenario ===")

        # Phase 1: Initial tests pass
        test_suite = TestSuite(
            name="Failure Recovery Tests",
            test_cases=[
                TestCase(
                    name="normal_test",
                    input_data={
                        "input": "normal processing",
                        "expected_format": "json",
                    },
                    expected_output="Processed 'normal processing' as json",
                    validation_rules=["exact_match"],
                )
            ],
        )

        test_runner.test_suite = test_suite
        initial_results = test_runner.run_test_suite()
        assert all(result.passed for result in initial_results)

        # Phase 2: Start rollout
        rollout_manager.start_rollout("model_v2.1.0")
        rollback_controller.start_monitoring("model_v2.1.0", "model_v2.0.5")

        # Phase 3: Introduce cascading failures
        print("Introducing cascading failures...")

        # First failure: Model starts producing errors
        mock_model.render.side_effect = ValueError("Model processing error")

        # Run tests again - should fail
        failing_results = test_runner.run_test_suite()
        assert not all(result.passed for result in failing_results)
        print(
            f"Test failures detected: {sum(1 for r in failing_results if not r.passed)} failed"
        )

        # Second failure: Performance regression
        def generate_degraded_performance_data():
            # Historical: good performance
            historical = [
                PerformanceData(
                    timestamp=datetime.now() - timedelta(hours=i),
                    metric_name="accuracy",
                    value=0.90 + np.random.normal(0, 0.01),
                    metadata={},
                )
                for i in range(1, 25)
            ]

            # Current: severely degraded performance
            current = [
                PerformanceData(
                    timestamp=datetime.now(),
                    metric_name="accuracy",
                    value=0.65 + np.random.normal(0, 0.02),  # Significant regression
                    metadata={},
                )
                for _ in range(10)
            ]

            return historical, current

        degraded_historical, degraded_current = generate_degraded_performance_data()

        # Health check should detect regression
        health = rollback_controller.check_health(degraded_historical, degraded_current)
        assert health.is_healthy is False
        assert health.triggers_rollback is True

        # Automatic rollback should trigger
        rollback_result = rollback_controller.trigger_automatic_rollback_if_needed(
            degraded_historical, degraded_current
        )

        assert rollback_result is not None
        assert rollback_result.success is True
        assert rollback_result.trigger == RollbackTrigger.PERFORMANCE_REGRESSION
        print(f"Automatic rollback completed in {rollback_result.duration:.2f}s")

        # Phase 4: Recovery
        print("Testing recovery mechanisms...")

        # Fix the model
        mock_model.render.side_effect = (
            lambda **kwargs: f"Recovered: {kwargs.get('input', 'test')}"
        )

        # Tests should pass again
        recovery_results = test_runner.run_test_suite()
        assert all(result.passed for result in recovery_results)
        print("Recovery successful - tests passing again")

        # Verify rollback history
        history = rollback_controller.get_rollback_history()
        assert len(history) == 1
        assert history[0].trigger == RollbackTrigger.PERFORMANCE_REGRESSION
        assert history[0].success is True

    def test_high_frequency_production_monitoring_pipeline(
        self, production_pipeline_components
    ):
        """Test high-frequency monitoring scenario simulating production load."""
        components = production_pipeline_components
        rollback_controller = components["rollback_controller"]
        components["regression_detector"]  # Available for monitoring

        print("\\n=== High-Frequency Production Monitoring ===")

        rollback_controller.start_monitoring("model_v2.1.0", "model_v2.0.5")

        # Simulate high-frequency monitoring (every 10 seconds for 2 minutes)
        monitoring_duration = 120  # 2 minutes
        check_interval = 10  # 10 seconds
        monitoring_results = []

        def generate_streaming_data(timestamp, has_issue=False):
            """Generate realistic streaming performance data."""
            base_values = {
                "accuracy": 0.88,
                "latency": 120,
                "throughput": 1000,
                "error_rate": 0.02,
            }

            if has_issue:
                # Simulate performance degradation
                base_values["accuracy"] *= 0.85  # 15% accuracy drop
                base_values["latency"] *= 1.4  # 40% latency increase
                base_values["throughput"] *= 0.7  # 30% throughput drop
                base_values["error_rate"] *= 3.0  # 3x error rate

            data_points = {}
            for metric_name, base_value in base_values.items():
                # Generate historical baseline (last 24 hours)
                historical = []
                for hour in range(24):
                    # Add realistic patterns (business hours, etc.)
                    hour_of_day = (timestamp - timedelta(hours=24 - hour)).hour
                    business_factor = 1.1 if 9 <= hour_of_day <= 17 else 1.0

                    if metric_name == "accuracy":
                        value = base_value + np.random.normal(0, 0.02) * business_factor
                        value = max(0, min(1, value))
                    elif metric_name == "latency":
                        value = base_value * business_factor + np.random.exponential(10)
                        value = max(0, value)
                    elif metric_name == "throughput":
                        value = base_value / business_factor + np.random.normal(0, 50)
                        value = max(0, value)
                    else:  # error_rate
                        value = base_value * business_factor + np.random.exponential(
                            0.005
                        )
                        value = max(0, min(1, value))

                    historical.append(
                        PerformanceData(
                            timestamp=timestamp - timedelta(hours=24 - hour),
                            metric_name=metric_name,
                            value=value,
                            metadata={"hour_of_day": hour_of_day},
                        )
                    )

                # Generate current data (last 10 minutes)
                current = []
                for minute in range(10):
                    if metric_name == "accuracy":
                        value = base_value + np.random.normal(0, 0.01)
                        value = max(0, min(1, value))
                    elif metric_name == "latency":
                        value = base_value + np.random.exponential(5)
                        value = max(0, value)
                    elif metric_name == "throughput":
                        value = base_value + np.random.normal(0, 30)
                        value = max(0, value)
                    else:  # error_rate
                        value = base_value + np.random.exponential(0.002)
                        value = max(0, min(1, value))

                    current.append(
                        PerformanceData(
                            timestamp=timestamp - timedelta(minutes=10 - minute),
                            metric_name=metric_name,
                            value=value,
                            metadata={"minute": minute},
                        )
                    )

                data_points[metric_name] = {
                    "historical": historical,
                    "current": current,
                }

            return data_points

        monitoring_start = time.time()
        checks_completed = 0
        rollbacks_triggered = 0

        for check_time in range(0, monitoring_duration, check_interval):
            check_start = time.time()
            current_timestamp = datetime.now() + timedelta(seconds=check_time)

            # Introduce issues at 60 seconds into monitoring
            has_performance_issue = check_time >= 60

            # Generate performance data
            perf_data = generate_streaming_data(
                current_timestamp, has_performance_issue
            )

            # Check health for each metric
            health_results = {}
            for metric_name, data in perf_data.items():
                health = rollback_controller.check_health(
                    data["historical"], data["current"]
                )
                health_results[metric_name] = health

                # Check for automatic rollback
                rollback_result = (
                    rollback_controller.trigger_automatic_rollback_if_needed(
                        data["historical"], data["current"]
                    )
                )

                if rollback_result is not None and rollback_result.success:
                    rollbacks_triggered += 1
                    print(
                        f"Rollback triggered for {metric_name} at check {checks_completed}"
                    )

            check_duration = time.time() - check_start

            monitoring_results.append(
                {
                    "check_id": checks_completed,
                    "timestamp": current_timestamp,
                    "check_duration": check_duration,
                    "health_results": health_results,
                    "has_issue": has_performance_issue,
                }
            )

            checks_completed += 1

            # Performance requirement: each monitoring cycle should be fast
            assert check_duration < 5.0, (
                f"Monitoring check took too long: {check_duration:.2f}s"
            )

            # Simulate real-time delay
            time.sleep(0.1)  # Small delay to simulate real monitoring

        total_monitoring_time = time.time() - monitoring_start

        # Analyze monitoring performance
        avg_check_time = sum(r["check_duration"] for r in monitoring_results) / len(
            monitoring_results
        )
        max_check_time = max(r["check_duration"] for r in monitoring_results)

        print(
            f"Completed {checks_completed} monitoring checks in {total_monitoring_time:.2f}s"
        )
        print(f"Average check time: {avg_check_time:.3f}s, Max: {max_check_time:.3f}s")
        print(f"Rollbacks triggered: {rollbacks_triggered}")

        # Performance requirements
        assert avg_check_time < 1.0, (
            f"Average monitoring too slow: {avg_check_time:.3f}s"
        )
        assert max_check_time < 3.0, f"Slowest monitoring check: {max_check_time:.3f}s"
        assert rollbacks_triggered > 0, "Should have triggered rollbacks during issues"

    def test_multi_environment_pipeline_coordination(
        self, production_pipeline_components
    ):
        """Test pipeline coordination across multiple environments (dev, staging, prod)."""
        production_pipeline_components  # Components available for multi-env

        print("\\n=== Multi-Environment Pipeline Coordination ===")

        environments = ["development", "staging", "production"]
        env_components = {}

        # Set up separate pipeline components for each environment
        for env in environments:
            mock_model = Mock()
            mock_model.name = f"{env}_model"
            mock_model.render.return_value = f"Processed in {env} environment"

            mock_registry = Mock()
            mock_registry.rollback_to_model.return_value = Mock(success=True)

            # Environment-specific configurations
            if env == "development":
                detector = PerformanceRegressionDetector(
                    significance_level=SignificanceLevel.ALPHA_10,  # Less strict for dev
                    minimum_samples=5,
                )
            elif env == "staging":
                detector = PerformanceRegressionDetector(
                    significance_level=SignificanceLevel.ALPHA_05,  # Standard for staging
                    minimum_samples=10,
                )
            else:  # production
                detector = PerformanceRegressionDetector(
                    significance_level=SignificanceLevel.ALPHA_01,  # Strict for prod
                    minimum_samples=20,
                )

            env_components[env] = {
                "test_runner": PromptTestRunner(mock_model),
                "rollout_manager": GradualRolloutManager(detector),
                "rollback_controller": RollbackController(detector, mock_registry),
                "detector": detector,
            }

        # Simulate coordinated deployment across environments
        deployment_results = {}

        for env in environments:
            print(f"\\nDeploying to {env} environment...")

            components_env = env_components[env]

            # Phase 1: Testing
            test_suite = TestSuite(
                name=f"{env}_deployment_tests",
                test_cases=[
                    TestCase(
                        name=f"{env}_basic_test",
                        input_data={"input": f"test in {env}"},
                        expected_output=f"Processed in {env} environment",
                        validation_rules=["exact_match"],
                    )
                ],
            )

            components_env["test_runner"].test_suite = test_suite
            test_results = components_env["test_runner"].run_test_suite()

            # Phase 2: Rollout
            rollout_result = components_env["rollout_manager"].start_rollout(
                f"model_v2.1.0_{env}"
            )
            components_env["rollback_controller"].start_monitoring(
                f"model_v2.1.0_{env}", f"model_v2.0.5_{env}"
            )

            # Phase 3: Health monitoring with environment-specific data
            def generate_env_specific_data(env_name):
                # Different performance characteristics per environment
                if env_name == "development":
                    base_accuracy = 0.80  # Lower accuracy in dev
                    base_latency = 200  # Higher latency in dev
                elif env_name == "staging":
                    base_accuracy = 0.85  # Medium accuracy in staging
                    base_latency = 150  # Medium latency in staging
                else:  # production
                    base_accuracy = 0.90  # High accuracy in prod
                    # base_latency = 100  # Low latency in prod (not used in test)

                historical = [
                    PerformanceData(
                        timestamp=datetime.now() - timedelta(hours=i),
                        metric_name="accuracy",
                        value=base_accuracy + np.random.normal(0, 0.02),
                        metadata={"environment": env_name},
                    )
                    for i in range(1, 25)
                ]

                current = [
                    PerformanceData(
                        timestamp=datetime.now(),
                        metric_name="accuracy",
                        value=base_accuracy
                        + 0.01
                        + np.random.normal(0, 0.01),  # Slight improvement
                        metadata={"environment": env_name},
                    )
                    for _ in range(10)
                ]

                return historical, current

            historical_data, current_data = generate_env_specific_data(env)

            # Health check
            health = components_env["rollback_controller"].check_health(
                historical_data, current_data
            )

            # Complete rollout if healthy
            rollout_success = True
            if health.is_healthy:
                # Progress through stages
                while components_env["rollout_manager"].is_active:
                    advance_result = components_env["rollout_manager"].advance_stage(
                        historical_data, current_data
                    )
                    if not advance_result.success:
                        rollout_success = False
                        break
            else:
                rollout_success = False

            deployment_results[env] = {
                "tests_passed": all(r.passed for r in test_results),
                "rollout_started": rollout_result.success,
                "health_check": health.is_healthy,
                "rollout_completed": rollout_success,
                "final_stage": components_env["rollout_manager"].current_stage,
            }

            print(f"{env} deployment result: {deployment_results[env]}")

        # Verify environment-specific requirements
        # Development: More lenient, focus on functionality
        dev_result = deployment_results["development"]
        assert dev_result["tests_passed"] is True
        assert dev_result["rollout_started"] is True

        # Staging: Balance of safety and speed
        staging_result = deployment_results["staging"]
        assert staging_result["tests_passed"] is True
        assert staging_result["rollout_completed"] is True

        # Production: Strict requirements
        prod_result = deployment_results["production"]
        assert prod_result["tests_passed"] is True
        assert prod_result["rollout_completed"] is True
        assert prod_result["final_stage"] == RolloutStage.FULL_ROLLOUT

        print("\\nMulti-environment deployment coordination completed successfully")

    def test_pipeline_performance_under_concurrent_deployments(
        self, production_pipeline_components
    ):
        """Test pipeline performance when handling multiple concurrent deployments."""
        production_pipeline_components  # Available for concurrent testing

        print("\\n=== Concurrent Deployments Performance Test ===")

        num_concurrent_deployments = 5
        deployment_results = []

        def run_concurrent_deployment(deployment_id: int):
            """Run a complete deployment pipeline."""
            deployment_start = time.time()

            try:
                # Create separate components for this deployment
                mock_model = Mock()
                mock_model.render.return_value = f"Deployment {deployment_id} output"

                mock_registry = Mock()
                mock_registry.rollback_to_model.return_value = Mock(success=True)

                detector = PerformanceRegressionDetector()
                test_runner = PromptTestRunner(mock_model)
                rollout_manager = GradualRolloutManager(detector)
                rollback_controller = RollbackController(detector, mock_registry)

                # Phase 1: Testing
                test_suite = TestSuite(
                    name=f"concurrent_deployment_{deployment_id}",
                    test_cases=[
                        TestCase(
                            name=f"test_{deployment_id}",
                            input_data={"deployment_id": deployment_id},
                            expected_output=f"Deployment {deployment_id} output",
                            validation_rules=["exact_match"],
                        )
                    ],
                )

                test_runner.test_suite = test_suite
                test_results = test_runner.run_test_suite()

                # Phase 2: Rollout
                rollout_result = rollout_manager.start_rollout(
                    f"model_v2.1.{deployment_id}"
                )
                rollback_controller.start_monitoring(
                    f"model_v2.1.{deployment_id}", f"model_v2.0.{deployment_id}"
                )

                # Phase 3: Complete rollout
                historical_data = [
                    PerformanceData(
                        timestamp=datetime.now() - timedelta(hours=i),
                        metric_name="accuracy",
                        value=0.85 + np.random.normal(0, 0.01),
                        metadata={"deployment_id": deployment_id},
                    )
                    for i in range(1, 13)
                ]

                current_data = [
                    PerformanceData(
                        timestamp=datetime.now(),
                        metric_name="accuracy",
                        value=0.87 + np.random.normal(0, 0.01),
                        metadata={"deployment_id": deployment_id},
                    )
                    for _ in range(5)
                ]

                # Progress through rollout stages
                stages_completed = 0
                while rollout_manager.is_active and stages_completed < 3:
                    advance_result = rollout_manager.advance_stage(
                        historical_data, current_data
                    )
                    if advance_result.success:
                        stages_completed += 1
                    else:
                        break

                deployment_duration = time.time() - deployment_start

                return {
                    "deployment_id": deployment_id,
                    "success": all(r.passed for r in test_results)
                    and rollout_result.success,
                    "duration": deployment_duration,
                    "stages_completed": stages_completed,
                    "final_stage": rollout_manager.current_stage,
                    "tests_passed": len([r for r in test_results if r.passed]),
                }

            except Exception as e:
                deployment_duration = time.time() - deployment_start
                return {
                    "deployment_id": deployment_id,
                    "success": False,
                    "duration": deployment_duration,
                    "error": str(e),
                }

        # Run concurrent deployments
        concurrent_start = time.time()

        with ThreadPoolExecutor(max_workers=num_concurrent_deployments) as executor:
            futures = [
                executor.submit(run_concurrent_deployment, i)
                for i in range(num_concurrent_deployments)
            ]

            deployment_results = [future.result() for future in futures]

        total_concurrent_time = time.time() - concurrent_start

        # Analyze results
        successful_deployments = [r for r in deployment_results if r["success"]]
        failed_deployments = [r for r in deployment_results if not r["success"]]

        avg_deployment_time = sum(r["duration"] for r in deployment_results) / len(
            deployment_results
        )
        max_deployment_time = max(r["duration"] for r in deployment_results)

        print(f"Concurrent deployments completed in {total_concurrent_time:.2f}s")
        print(f"Successful: {len(successful_deployments)}/{num_concurrent_deployments}")
        print(f"Average deployment time: {avg_deployment_time:.2f}s")
        print(f"Maximum deployment time: {max_deployment_time:.2f}s")

        # Performance requirements for concurrent deployments
        assert len(successful_deployments) == num_concurrent_deployments, (
            "All deployments should succeed"
        )
        assert len(failed_deployments) == 0, (
            f"No deployments should fail: {failed_deployments}"
        )
        assert avg_deployment_time < 30.0, (
            f"Average deployment too slow: {avg_deployment_time:.2f}s"
        )
        assert max_deployment_time < 60.0, (
            f"Slowest deployment too slow: {max_deployment_time:.2f}s"
        )
        assert total_concurrent_time < 120.0, (
            f"Total concurrent time too long: {total_concurrent_time:.2f}s"
        )

        # Verify all deployments reached full rollout
        for result in successful_deployments:
            assert result["stages_completed"] == 3, (
                f"Deployment {result['deployment_id']} didn't complete all stages"
            )
            assert result["final_stage"] == RolloutStage.FULL_ROLLOUT


@pytest.mark.performance
class TestCICDPipelinePerformanceRequirements:
    """Test pipeline-wide performance requirements and SLAs."""

    def test_end_to_end_pipeline_performance_sla(self, production_pipeline_components):
        """Test complete pipeline meets end-to-end performance SLA."""
        components = production_pipeline_components

        # Performance SLA requirements
        MAX_PIPELINE_DURATION = 180  # 3 minutes max for complete pipeline
        MAX_TEST_PHASE_DURATION = 30  # 30 seconds for testing phase
        MAX_ROLLOUT_PHASE_DURATION = 120  # 2 minutes for rollout phase
        # MAX_ROLLBACK_DURATION = 30  # 30 seconds for rollback if needed (not used)

        pipeline_start = time.time()

        # Phase timing measurements
        phase_times = {}

        # Testing Phase
        test_start = time.time()

        test_suite = TestSuite(
            name="Performance SLA Tests",
            test_cases=[
                TestCase(
                    name="sla_test_1",
                    input_data={"input": "performance test", "expected_format": "json"},
                    expected_output="Processed 'performance test' as json",
                    validation_rules=["exact_match", "max_execution_time:0.5"],
                ),
                TestCase(
                    name="sla_test_2",
                    input_data={"input": "load test", "expected_format": "xml"},
                    expected_output="Processed 'load test' as xml",
                    validation_rules=["exact_match", "max_execution_time:0.5"],
                ),
            ],
        )

        components["test_runner"].test_suite = test_suite
        components["test_runner"].run_test_suite()

        phase_times["testing"] = time.time() - test_start

        # Rollout Phase
        rollout_start = time.time()

        components["rollout_manager"].start_rollout("model_v2.1.0")
        components["rollback_controller"].start_monitoring(
            "model_v2.1.0", "model_v2.0.5"
        )

        # Generate performance data
        historical_data = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(hours=i),
                metric_name="accuracy",
                value=0.85 + np.random.normal(0, 0.01),
                metadata={},
            )
            for i in range(1, 25)
        ]

        current_data = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.87 + np.random.normal(0, 0.01),
                metadata={},
            )
            for _ in range(10)
        ]

        # Complete rollout
        while components["rollout_manager"].is_active:
            advance_result = components["rollout_manager"].advance_stage(
                historical_data, current_data
            )
            assert advance_result.success is True

        phase_times["rollout"] = time.time() - rollout_start

        total_pipeline_time = time.time() - pipeline_start

        # Verify SLA compliance
        assert phase_times["testing"] < MAX_TEST_PHASE_DURATION, (
            f"Testing phase too slow: {phase_times['testing']:.2f}s"
        )
        assert phase_times["rollout"] < MAX_ROLLOUT_PHASE_DURATION, (
            f"Rollout phase too slow: {phase_times['rollout']:.2f}s"
        )
        assert total_pipeline_time < MAX_PIPELINE_DURATION, (
            f"Total pipeline too slow: {total_pipeline_time:.2f}s"
        )

        print("Pipeline SLA compliance verified:")
        print(
            f"  Testing phase: {phase_times['testing']:.2f}s (< {MAX_TEST_PHASE_DURATION}s)"
        )
        print(
            f"  Rollout phase: {phase_times['rollout']:.2f}s (< {MAX_ROLLOUT_PHASE_DURATION}s)"
        )
        print(
            f"  Total pipeline: {total_pipeline_time:.2f}s (< {MAX_PIPELINE_DURATION}s)"
        )

    def test_pipeline_throughput_requirements(self, production_pipeline_components):
        """Test pipeline throughput meets production requirements."""
        components = production_pipeline_components

        # Throughput requirements
        # MIN_DEPLOYMENTS_PER_HOUR = 10  # Not used in current test
        MIN_TESTS_PER_MINUTE = 100
        MIN_HEALTH_CHECKS_PER_MINUTE = 60

        # Test throughput
        test_start = time.time()
        # tests_completed = 0  # Counter not used

        test_suite = TestSuite(
            name="Throughput Test",
            test_cases=[
                TestCase(
                    name=f"throughput_test_{i}",
                    input_data={"input": f"test {i}"},
                    expected_output=f"Processed 'test {i}' as json",
                    validation_rules=["contains:test"],
                )
                for i in range(200)  # 200 test cases
            ],
        )

        components["test_runner"].test_suite = test_suite
        test_results = components["test_runner"].run_test_suite()

        test_duration = time.time() - test_start
        tests_per_minute = len(test_results) / (test_duration / 60)

        # Health check throughput
        health_check_start = time.time()
        health_checks_completed = 0

        components["rollback_controller"].start_monitoring(
            "model_v2.1.0", "model_v2.0.5"
        )

        historical_data = [Mock(metric_name="accuracy") for _ in range(20)]
        current_data = [Mock(metric_name="accuracy") for _ in range(10)]

        # Configure detector
        components["regression_detector"].detect_regression = Mock(
            return_value=Mock(is_regression=False, p_value=0.8)
        )

        while time.time() - health_check_start < 60:  # 1 minute of health checks
            components["rollback_controller"].check_health(
                historical_data, current_data
            )
            health_checks_completed += 1

        health_check_duration = time.time() - health_check_start
        health_checks_per_minute = health_checks_completed / (
            health_check_duration / 60
        )

        # Verify throughput requirements
        assert tests_per_minute >= MIN_TESTS_PER_MINUTE, (
            f"Test throughput too low: {tests_per_minute:.1f}/min"
        )
        assert health_checks_per_minute >= MIN_HEALTH_CHECKS_PER_MINUTE, (
            f"Health check throughput too low: {health_checks_per_minute:.1f}/min"
        )

        print("Throughput requirements met:")
        print(f"  Tests per minute: {tests_per_minute:.1f} (>= {MIN_TESTS_PER_MINUTE})")
        print(
            f"  Health checks per minute: {health_checks_per_minute:.1f} (>= {MIN_HEALTH_CHECKS_PER_MINUTE})"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
