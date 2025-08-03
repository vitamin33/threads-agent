"""
Advanced failure scenarios test suite for GradualRolloutManager.

This suite focuses on:
- Failure injection and error resilience
- Network partition and service unavailability scenarios
- Race conditions and concurrent rollout conflicts
- Recovery and rollback scenarios
- Performance degradation and timeout handling
- Resource exhaustion scenarios

Author: Test Generation Specialist for CRA-297
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from services.common.gradual_rollout_manager import (
    GradualRolloutManager,
    RolloutStage,
    RolloutResult,
)


class TestGradualRolloutManagerFailureInjection:
    """Test failure injection scenarios for rollout manager."""

    @pytest.fixture
    def failing_performance_detector(self):
        """Mock detector that simulates various failure modes."""
        detector = Mock()

        def failing_detect_regression(*args, **kwargs):
            failure_mode = kwargs.get("failure_mode", "none")

            if failure_mode == "timeout":
                time.sleep(5)  # Simulate timeout
                raise TimeoutError("Performance detector timeout")
            elif failure_mode == "network_error":
                raise ConnectionError("Unable to connect to metrics store")
            elif failure_mode == "memory_error":
                raise MemoryError("Out of memory during analysis")
            elif failure_mode == "data_corruption":
                raise ValueError("Corrupted performance data detected")
            elif failure_mode == "intermittent":
                import random

                if random.random() < 0.3:  # 30% failure rate
                    raise RuntimeError("Intermittent analysis failure")
                return Mock(is_regression=False, p_value=0.8)
            else:
                return Mock(is_regression=False, p_value=0.8)

        detector.detect_regression.side_effect = failing_detect_regression
        return detector

    def test_rollout_resilience_to_detector_timeout(self, failing_performance_detector):
        """Test rollout continues gracefully when detector times out."""
        manager = GradualRolloutManager(failing_performance_detector)
        manager.start_rollout("model_v2.0")

        # Create test data that will cause timeout
        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]

        # Mock the failure mode
        failing_performance_detector.detect_regression.side_effect = TimeoutError(
            "Timeout"
        )

        # Advance stage should handle timeout gracefully
        result = manager.advance_stage(historical_data, current_data)

        # Should still advance but without health check validation
        assert result.success is True
        assert manager.current_stage == RolloutStage.CANARY_25

    def test_rollout_blocks_on_network_failures(self, failing_performance_detector):
        """Test rollout blocks when network failures occur during health checks."""
        manager = GradualRolloutManager(failing_performance_detector)
        manager.start_rollout("model_v2.0")

        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]

        # Simulate network failure
        failing_performance_detector.detect_regression.side_effect = ConnectionError(
            "Network error"
        )

        result = manager.advance_stage(historical_data, current_data)

        # Should block advancement on network failures (can't verify health)
        assert result.success is False
        assert (
            "network" in result.error_message.lower()
            or "connection" in result.error_message.lower()
        )
        assert manager.current_stage == RolloutStage.CANARY_10

    def test_rollout_recovery_after_intermittent_failures(
        self, failing_performance_detector
    ):
        """Test rollout recovery after intermittent failures."""
        manager = GradualRolloutManager(failing_performance_detector)
        manager.start_rollout("model_v2.0")

        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]

        # Configure intermittent failures
        def intermittent_failure(*args, **kwargs):
            if not hasattr(intermittent_failure, "call_count"):
                intermittent_failure.call_count = 0
            intermittent_failure.call_count += 1

            # Fail first 3 calls, then succeed
            if intermittent_failure.call_count <= 3:
                raise RuntimeError(
                    f"Intermittent failure #{intermittent_failure.call_count}"
                )
            return Mock(is_regression=False, p_value=0.8)

        failing_performance_detector.detect_regression.side_effect = (
            intermittent_failure
        )

        # Multiple attempts should eventually succeed
        results = []
        for attempt in range(5):
            try:
                result = manager.advance_stage(historical_data, current_data)
                results.append(result)
                if result.success:
                    break
            except RuntimeError:
                continue

        # Should eventually succeed after intermittent failures
        assert any(r.success for r in results), (
            "Should recover from intermittent failures"
        )

    def test_memory_pressure_during_rollout(self, failing_performance_detector):
        """Test rollout behavior under memory pressure."""
        manager = GradualRolloutManager(failing_performance_detector)
        manager.start_rollout("model_v2.0")

        # Simulate memory pressure by creating large data
        large_historical_data = []
        for i in range(10000):  # Large dataset
            large_historical_data.append(
                Mock(
                    metric_name="accuracy",
                    value=0.85,
                    timestamp=datetime.now() - timedelta(hours=i),
                    metadata={"large_data": "x" * 1024},  # 1KB per record
                )
            )

        current_data = [Mock(metric_name="accuracy")]

        # Configure memory error
        failing_performance_detector.detect_regression.side_effect = MemoryError(
            "Out of memory"
        )

        result = manager.advance_stage(large_historical_data, current_data)

        # Should handle memory errors gracefully
        assert result.success is False
        assert "memory" in result.error_message.lower()

    def test_data_corruption_detection_during_rollout(
        self, failing_performance_detector
    ):
        """Test rollout response to data corruption detection."""
        manager = GradualRolloutManager(failing_performance_detector)
        manager.start_rollout("model_v2.0")

        # Create corrupted data
        corrupted_data = [
            Mock(metric_name="accuracy", value=float("inf")),
            Mock(metric_name="accuracy", value=float("nan")),
            Mock(metric_name="accuracy", value=-999.0),
        ]

        current_data = [Mock(metric_name="accuracy")]

        # Configure data corruption error
        failing_performance_detector.detect_regression.side_effect = ValueError(
            "Corrupted data"
        )

        result = manager.advance_stage(corrupted_data, current_data)

        # Should block rollout on data corruption
        assert result.success is False
        assert (
            "corrupt" in result.error_message.lower()
            or "invalid" in result.error_message.lower()
        )


class TestGradualRolloutManagerConcurrencyAndRaceConditions:
    """Test concurrent operations and race condition scenarios."""

    def test_concurrent_rollout_start_prevention(self):
        """Test prevention of concurrent rollout starts."""
        detector = Mock()
        detector.detect_regression.return_value = Mock(is_regression=False)

        manager = GradualRolloutManager(detector)

        results = []
        errors = []

        def start_rollout_worker(model_version):
            try:
                result = manager.start_rollout(f"model_{model_version}")
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        # Start multiple rollouts concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=start_rollout_worker, args=(f"v2.{i}",))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Only one rollout should succeed
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        assert len(successful_results) == 1, "Only one rollout should succeed"
        assert len(failed_results) == 9, "Other rollouts should fail"
        assert len(errors) == 0, "No exceptions should be raised"

    def test_concurrent_stage_advancement_safety(self):
        """Test safety of concurrent stage advancement operations."""
        detector = Mock()
        detector.detect_regression.return_value = Mock(is_regression=False)

        manager = GradualRolloutManager(detector)
        manager.start_rollout("model_v2.0")

        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]

        results = []

        def advance_stage_worker():
            try:
                result = manager.advance_stage(historical_data, current_data)
                results.append(result)
            except Exception as e:
                results.append(
                    RolloutResult(
                        success=False,
                        stage=manager.current_stage,
                        traffic_percentage=manager.traffic_percentage,
                        error_message=str(e),
                    )
                )

        # Advance stages concurrently
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=advance_stage_worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Should handle concurrent access safely
        assert len(results) == 5
        successful_advances = [r for r in results if r.success]

        # Some operations should succeed, but stage should be consistent
        assert (
            len(successful_advances) <= 4
        )  # Maximum possible advances from CANARY_10 to FULL_ROLLOUT

    def test_rollout_state_consistency_under_load(self):
        """Test rollout state consistency under high load."""
        detector = Mock()
        detector.detect_regression.return_value = Mock(is_regression=False)

        manager = GradualRolloutManager(detector)
        manager.start_rollout("model_v2.0")

        # Simulate high load with many status checks and operations
        results = []

        def mixed_operations_worker(worker_id):
            worker_results = []
            historical_data = [Mock(metric_name="accuracy")]
            current_data = [Mock(metric_name="accuracy")]

            for i in range(10):
                try:
                    if i % 3 == 0:
                        # Status check
                        status = manager.get_rollout_status()
                        worker_results.append(("status", status))
                    elif i % 3 == 1:
                        # Health monitoring
                        health = manager.monitor_deployment_health(
                            historical_data, current_data
                        )
                        worker_results.append(("health", health))
                    else:
                        # Stage advancement attempt
                        result = manager.advance_stage(historical_data, current_data)
                        worker_results.append(("advance", result))
                except Exception as e:
                    worker_results.append(("error", str(e)))

            return worker_results

        # Run mixed operations concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(mixed_operations_worker, i) for i in range(10)]

            for future in futures:
                results.extend(future.result())

        # Verify state consistency
        final_status = manager.get_rollout_status()

        # State should be valid
        assert final_status.current_stage in [
            RolloutStage.CANARY_10,
            RolloutStage.CANARY_25,
            RolloutStage.CANARY_50,
            RolloutStage.FULL_ROLLOUT,
        ]
        assert (
            final_status.traffic_percentage
            == final_status.current_stage.traffic_percentage
        )

    def test_rollout_interruption_and_cleanup(self):
        """Test rollout interruption and proper cleanup."""
        detector = Mock()
        detector.detect_regression.return_value = Mock(is_regression=False)

        manager = GradualRolloutManager(detector)
        manager.start_rollout("model_v2.0")

        # Simulate sudden interruption during rollout
        def interrupt_rollout():
            time.sleep(0.1)  # Let rollout start
            # Simulate various interruption scenarios
            manager.is_active = False  # Simulate external interruption

        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]

        # Start interruption in background
        interrupt_thread = threading.Thread(target=interrupt_rollout)
        interrupt_thread.start()

        # Try to advance stages while being interrupted
        results = []
        for _ in range(3):
            try:
                result = manager.advance_stage(historical_data, current_data)
                results.append(result)
                time.sleep(0.05)
            except Exception as e:
                results.append(
                    RolloutResult(
                        success=False,
                        stage=manager.current_stage,
                        traffic_percentage=manager.traffic_percentage,
                        error_message=str(e),
                    )
                )

        interrupt_thread.join()

        # Should handle interruption gracefully
        final_status = manager.get_rollout_status()
        assert final_status.is_active is False


class TestGradualRolloutManagerRecoveryScenarios:
    """Test recovery scenarios and error handling."""

    def test_rollout_recovery_after_service_restart(self):
        """Test rollout state recovery after service restart simulation."""
        detector = Mock()
        detector.detect_regression.return_value = Mock(is_regression=False)

        # First manager instance - start rollout
        manager1 = GradualRolloutManager(detector)
        manager1.start_rollout("model_v2.0")

        # Advance to 25% stage
        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]
        result1 = manager1.advance_stage(historical_data, current_data)
        assert result1.success is True
        assert manager1.current_stage == RolloutStage.CANARY_25

        # Save state information
        saved_stage = manager1.current_stage
        saved_traffic = manager1.traffic_percentage
        saved_model = manager1.model_version
        saved_start_time = manager1.start_time

        # Simulate service restart - new manager instance
        manager2 = GradualRolloutManager(detector)

        # Restore state (in real implementation, this would be from persistent storage)
        manager2.current_stage = saved_stage
        manager2.traffic_percentage = saved_traffic
        manager2.model_version = saved_model
        manager2.start_time = saved_start_time
        manager2.is_active = True

        # Should be able to continue rollout
        result2 = manager2.advance_stage(historical_data, current_data)
        assert result2.success is True
        assert manager2.current_stage == RolloutStage.CANARY_50

    def test_rollout_timeout_handling_and_recovery(self):
        """Test rollout timeout handling and recovery mechanisms."""
        detector = Mock()
        detector.detect_regression.return_value = Mock(is_regression=False)

        manager = GradualRolloutManager(
            detector, stage_timeout_minutes=1
        )  # 1 minute timeout

        # Start rollout
        with patch("services.common.gradual_rollout_manager.datetime") as mock_datetime:
            start_time = datetime.now()
            mock_datetime.now.return_value = start_time

            result = manager.start_rollout("model_v2.0")
            assert result.success is True

            # Advance time to cause timeout
            timeout_time = start_time + timedelta(minutes=2)
            mock_datetime.now.return_value = timeout_time

            # Check timeout status
            status = manager.get_rollout_status()
            assert status.is_timed_out is True

            # Rollout should still be active but marked as timed out
            assert status.is_active is True
            assert status.current_stage == RolloutStage.CANARY_10

    def test_rollout_recovery_from_partial_failure(self):
        """Test recovery from partial failure scenarios."""
        detector = Mock()

        # Configure detector to fail then succeed
        def progressive_detector(*args, **kwargs):
            if not hasattr(progressive_detector, "call_count"):
                progressive_detector.call_count = 0
            progressive_detector.call_count += 1

            if progressive_detector.call_count <= 2:
                # First 2 calls indicate regression (failure)
                return Mock(is_regression=True, p_value=0.01)
            else:
                # Later calls indicate no regression (recovery)
                return Mock(is_regression=False, p_value=0.8)

        detector.detect_regression.side_effect = progressive_detector

        manager = GradualRolloutManager(detector)
        manager.start_rollout("model_v2.0")

        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]

        # First attempt should fail due to regression
        result1 = manager.advance_stage(historical_data, current_data)
        assert result1.success is False
        assert "regression" in result1.error_message.lower()
        assert manager.current_stage == RolloutStage.CANARY_10

        # Second attempt should also fail
        result2 = manager.advance_stage(historical_data, current_data)
        assert result2.success is False

        # Third attempt should succeed (recovery)
        result3 = manager.advance_stage(historical_data, current_data)
        assert result3.success is True
        assert manager.current_stage == RolloutStage.CANARY_25

    def test_rollout_rollback_on_consecutive_failures(self):
        """Test rollout rollback mechanism on consecutive failures."""
        detector = Mock()
        detector.detect_regression.return_value = Mock(
            is_regression=True, p_value=0.001
        )

        manager = GradualRolloutManager(detector)
        manager.start_rollout("model_v2.0")

        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]

        # Multiple consecutive failures
        failed_attempts = []
        for attempt in range(5):
            result = manager.advance_stage(historical_data, current_data)
            failed_attempts.append(result)

            # Should fail each time due to regression
            assert result.success is False
            assert "regression" in result.error_message.lower()
            assert manager.current_stage == RolloutStage.CANARY_10  # Should not advance

        # All attempts should fail consistently
        assert all(not attempt.success for attempt in failed_attempts)

        # Rollout should still be active but stuck at first stage
        status = manager.get_rollout_status()
        assert status.is_active is True
        assert status.current_stage == RolloutStage.CANARY_10


class TestGradualRolloutManagerResourceExhaustion:
    """Test resource exhaustion and performance degradation scenarios."""

    def test_rollout_under_cpu_pressure(self):
        """Test rollout behavior under CPU pressure."""
        detector = Mock()

        def cpu_intensive_detection(*args, **kwargs):
            # Simulate CPU-intensive operation
            start_time = time.time()
            while time.time() - start_time < 0.5:  # 500ms of computation
                _ = sum(i * i for i in range(1000))
            return Mock(is_regression=False, p_value=0.8)

        detector.detect_regression.side_effect = cpu_intensive_detection

        manager = GradualRolloutManager(detector)
        manager.start_rollout("model_v2.0")

        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]

        # Measure rollout performance under CPU load
        start_time = time.time()
        result = manager.advance_stage(historical_data, current_data)
        execution_time = time.time() - start_time

        # Should complete despite CPU pressure
        assert result.success is True
        assert execution_time > 0.5  # Should take time due to CPU load
        assert execution_time < 5.0  # But not excessively long

    def test_rollout_memory_usage_monitoring(self):
        """Test rollout memory usage patterns."""
        import psutil
        import gc

        detector = Mock()
        detector.detect_regression.return_value = Mock(is_regression=False, p_value=0.8)

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        manager = GradualRolloutManager(detector)

        # Perform multiple rollout operations
        memory_measurements = []

        for rollout_id in range(10):
            # Start rollout
            manager.start_rollout(f"model_v{rollout_id}")

            # Create large test data
            large_historical_data = [
                Mock(
                    metric_name="accuracy",
                    value=0.85,
                    metadata={"data": "x" * 10240},  # 10KB per record
                )
                for _ in range(100)
            ]

            current_data = [Mock(metric_name="accuracy")]

            # Advance through stages
            for _ in range(3):  # Advance 3 stages
                try:
                    manager.advance_stage(large_historical_data, current_data)
                except Exception:
                    pass  # Ignore errors for memory test

            # Measure memory
            current_memory = process.memory_info().rss
            memory_measurements.append(current_memory - initial_memory)

            # Reset for next iteration
            manager.is_active = False
            manager.current_stage = RolloutStage.PREPARATION

            # Force cleanup
            del large_historical_data
            gc.collect()

        # Memory usage should not grow excessively
        final_memory_increase = memory_measurements[-1]
        assert final_memory_increase < 100 * 1024 * 1024  # Less than 100MB increase

    def test_rollout_with_slow_performance_detector(self):
        """Test rollout resilience to slow performance detector."""
        detector = Mock()

        def slow_detection(*args, **kwargs):
            time.sleep(2)  # 2 second delay
            return Mock(is_regression=False, p_value=0.8)

        detector.detect_regression.side_effect = slow_detection

        manager = GradualRolloutManager(detector)
        manager.start_rollout("model_v2.0")

        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]

        # Measure total rollout time with slow detector
        start_time = time.time()

        # Advance through all stages
        stages_completed = 0
        while manager.is_active and stages_completed < 4:
            result = manager.advance_stage(historical_data, current_data)
            if result.success:
                stages_completed += 1

        total_time = time.time() - start_time

        # Should complete despite slow detector
        assert manager.current_stage == RolloutStage.FULL_ROLLOUT
        assert total_time > 6.0  # Should take time due to slow detector
        assert total_time < 15.0  # But should complete in reasonable time

    def test_rollout_network_latency_impact(self):
        """Test rollout behavior with network latency simulation."""
        detector = Mock()

        def network_latent_detection(*args, **kwargs):
            # Simulate network latency
            import random

            latency = random.uniform(0.1, 1.0)  # 100ms to 1s latency
            time.sleep(latency)
            return Mock(is_regression=False, p_value=0.8)

        detector.detect_regression.side_effect = network_latent_detection

        manager = GradualRolloutManager(detector)
        manager.start_rollout("model_v2.0")

        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]

        # Perform multiple stage advances with variable latency
        latencies = []
        for _ in range(3):
            start_time = time.time()
            result = manager.advance_stage(historical_data, current_data)
            latency = time.time() - start_time
            latencies.append(latency)

            assert result.success is True

        # Should handle variable network latency
        assert all(0.1 <= lat <= 2.0 for lat in latencies)
        assert manager.current_stage == RolloutStage.FULL_ROLLOUT


@pytest.mark.performance
class TestGradualRolloutManagerPerformanceRequirements:
    """Test specific performance requirements for rollout operations."""

    def test_stage_advancement_latency_requirements(self):
        """Test stage advancement latency requirements."""
        detector = Mock()
        detector.detect_regression.return_value = Mock(is_regression=False, p_value=0.8)

        manager = GradualRolloutManager(detector)
        manager.start_rollout("model_v2.0")

        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]

        # Measure stage advancement latencies
        advancement_times = []

        for _ in range(3):  # Advance 3 stages
            start_time = time.time()
            result = manager.advance_stage(historical_data, current_data)
            advancement_time = time.time() - start_time
            advancement_times.append(advancement_time)

            assert result.success is True

        # Performance requirements
        max_advancement_time = max(advancement_times)
        avg_advancement_time = sum(advancement_times) / len(advancement_times)

        assert max_advancement_time < 5.0  # Maximum 5 seconds per stage
        assert avg_advancement_time < 2.0  # Average under 2 seconds

    def test_rollout_throughput_requirements(self):
        """Test rollout throughput under load."""
        detector = Mock()
        detector.detect_regression.return_value = Mock(is_regression=False, p_value=0.8)

        # Measure rollout completion times
        completion_times = []

        for rollout_id in range(5):  # 5 complete rollouts
            manager = GradualRolloutManager(detector)

            start_time = time.time()
            manager.start_rollout(f"model_v{rollout_id}")

            historical_data = [Mock(metric_name="accuracy")]
            current_data = [Mock(metric_name="accuracy")]

            # Complete full rollout
            while manager.is_active:
                result = manager.advance_stage(historical_data, current_data)
                if not result.success:
                    break

            completion_time = time.time() - start_time
            completion_times.append(completion_time)

        # Throughput requirements
        avg_completion_time = sum(completion_times) / len(completion_times)
        max_completion_time = max(completion_times)

        assert avg_completion_time < 10.0  # Average rollout under 10 seconds
        assert max_completion_time < 15.0  # Maximum rollout under 15 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
