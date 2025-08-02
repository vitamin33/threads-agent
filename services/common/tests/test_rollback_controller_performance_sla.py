"""
Performance SLA and stress testing for RollbackController - <30s rollback requirement.

This suite focuses on:
- <30 second rollback SLA validation
- High-frequency health monitoring performance
- Concurrent rollback scenarios and thread safety
- Memory and resource efficiency under load
- Recovery time measurement and optimization
- Real-world production scenario simulation

Author: Test Generation Specialist for CRA-297
"""

import pytest
import time
import threading
import psutil
import gc
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.common.rollback_controller import (
    RollbackController,
    RollbackTrigger,
    RollbackError,
    RollbackStatus,
    RollbackResult,
    RollbackEvent,
    HealthCheck
)
from services.common.performance_regression_detector import (
    PerformanceRegressionDetector,
    PerformanceData,
    MetricType
)


class TestRollbackControllerPerformanceSLA:
    """Test critical <30s rollback SLA requirement."""

    @pytest.fixture
    def fast_mock_components(self):
        """Mock components optimized for fast execution."""
        detector = Mock()
        detector.detect_regression.return_value = Mock(
            is_regression=True,
            is_significant_change=True,
            p_value=0.001
        )
        
        registry = Mock()
        # Simulate fast rollback execution
        registry.rollback_to_model.return_value = Mock(success=True)
        
        return detector, registry

    def test_manual_rollback_sla_compliance(self, fast_mock_components):
        """Test manual rollback completes within 30 seconds (critical SLA)."""
        detector, registry = fast_mock_components
        controller = RollbackController(detector, registry)
        
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Measure rollback execution time
        start_time = time.time()
        result = controller.execute_manual_rollback("Critical performance issue")
        execution_time = time.time() - start_time
        
        # Critical SLA requirement
        assert result.success is True
        assert execution_time < 30.0, f"Rollback took {execution_time:.2f}s, exceeds 30s SLA"
        assert result.duration < 30.0, f"Reported duration {result.duration:.2f}s exceeds SLA"
        
        # Verify rollback was actually executed
        registry.rollback_to_model.assert_called_once_with("model_v1.9")

    def test_automatic_rollback_sla_compliance(self, fast_mock_components):
        """Test automatic rollback triggers within 30 seconds."""
        detector, registry = fast_mock_components
        controller = RollbackController(detector, registry)
        
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Create regression data
        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]
        
        # Measure automatic rollback time
        start_time = time.time()
        rollback_result = controller.trigger_automatic_rollback_if_needed(
            historical_data, current_data
        )
        execution_time = time.time() - start_time
        
        # SLA compliance
        assert rollback_result is not None
        assert rollback_result.success is True
        assert execution_time < 30.0, f"Automatic rollback took {execution_time:.2f}s"
        assert rollback_result.duration < 30.0

    def test_rollback_sla_under_memory_pressure(self, fast_mock_components):
        """Test rollback SLA compliance under memory pressure."""
        detector, registry = fast_mock_components
        controller = RollbackController(detector, registry)
        
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Create memory pressure
        large_objects = []
        try:
            for _ in range(100):
                large_objects.append(bytearray(1024 * 1024))  # 1MB each
            
            # Execute rollback under memory pressure
            start_time = time.time()
            result = controller.execute_manual_rollback("Memory pressure test")
            execution_time = time.time() - start_time
            
            # Should still meet SLA under memory pressure
            assert result.success is True
            assert execution_time < 30.0, f"Rollback under memory pressure took {execution_time:.2f}s"
            
        except MemoryError:
            pytest.skip("Insufficient memory for pressure testing")
        finally:
            del large_objects
            gc.collect()

    def test_rollback_sla_with_slow_registry(self, fast_mock_components):
        """Test rollback SLA when model registry is slow."""
        detector, registry = fast_mock_components
        
        # Mock slow registry response
        def slow_rollback(model_version):
            time.sleep(20)  # 20 second delay
            return Mock(success=True)
        
        registry.rollback_to_model.side_effect = slow_rollback
        
        controller = RollbackController(detector, registry)
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Test with slow registry
        start_time = time.time()
        result = controller.execute_manual_rollback("Slow registry test")
        execution_time = time.time() - start_time
        
        # Should still complete (though close to SLA limit)
        assert result.success is True
        assert execution_time < 30.0, f"Rollback with slow registry took {execution_time:.2f}s"
        assert 20.0 <= execution_time <= 25.0  # Should reflect registry delay

    def test_rollback_sla_batch_processing(self, fast_mock_components):
        """Test rollback SLA for batch rollback scenarios."""
        detector, registry = fast_mock_components
        controller = RollbackController(detector, registry)
        
        # Start monitoring
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Simulate batch rollback scenario (multiple services)
        rollback_times = []
        
        for batch_id in range(5):
            start_time = time.time()
            result = controller.execute_manual_rollback(f"Batch rollback {batch_id}")
            execution_time = time.time() - start_time
            rollback_times.append(execution_time)
            
            assert result.success is True
            assert execution_time < 30.0
            
            # Reset state for next rollback
            controller.stop_monitoring()
            controller.start_monitoring(f"model_v2.{batch_id}", "model_v1.9")
        
        # All rollbacks should meet SLA
        max_rollback_time = max(rollback_times)
        avg_rollback_time = sum(rollback_times) / len(rollback_times)
        
        assert max_rollback_time < 30.0
        assert avg_rollback_time < 15.0  # Average should be much faster


class TestRollbackControllerHighFrequencyMonitoring:
    """Test high-frequency health monitoring performance."""

    @pytest.fixture
    def monitoring_components(self):
        """Components optimized for monitoring testing."""
        detector = Mock()
        registry = Mock()
        registry.rollback_to_model.return_value = Mock(success=True)
        
        return detector, registry

    def test_high_frequency_health_checks(self, monitoring_components):
        """Test health check performance at high frequency."""
        detector, registry = monitoring_components
        controller = RollbackController(detector, registry, health_check_interval_seconds=1)
        
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Simulate high-frequency health checks
        health_check_times = []
        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]
        
        for _ in range(100):  # 100 health checks
            start_time = time.time()
            
            # Configure detector response
            detector.detect_regression.return_value = Mock(
                is_regression=False,
                is_significant_change=False,
                p_value=0.8
            )
            
            health = controller.check_health(historical_data, current_data)
            check_time = time.time() - start_time
            health_check_times.append(check_time)
            
            assert health is not None
            assert health.is_healthy is True
        
        # Performance requirements for health checks
        max_check_time = max(health_check_times)
        avg_check_time = sum(health_check_times) / len(health_check_times)
        
        assert max_check_time < 1.0,  f"Slowest health check: {max_check_time:.3f}s"
        assert avg_check_time < 0.1,  f"Average health check: {avg_check_time:.3f}s"

    def test_continuous_monitoring_performance(self, monitoring_components):
        """Test continuous monitoring over extended period."""
        detector, registry = monitoring_components
        controller = RollbackController(detector, registry)
        
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Configure detector for no regression
        detector.detect_regression.return_value = Mock(
            is_regression=False,
            p_value=0.8
        )
        
        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]
        
        # Run continuous monitoring simulation
        monitoring_start = time.time()
        health_checks_completed = 0
        
        while time.time() - monitoring_start < 10.0:  # 10 seconds of monitoring
            health = controller.check_health(historical_data, current_data)
            assert health.is_healthy is True
            health_checks_completed += 1
            
            time.sleep(0.01)  # 10ms between checks
        
        monitoring_duration = time.time() - monitoring_start
        
        # Performance metrics
        checks_per_second = health_checks_completed / monitoring_duration
        
        assert checks_per_second > 50,  f"Low throughput: {checks_per_second:.1f} checks/sec"
        assert health_checks_completed > 500,  "Should complete many health checks"

    def test_monitoring_memory_efficiency(self, monitoring_components):
        """Test memory efficiency during extended monitoring."""
        detector, registry = monitoring_components
        controller = RollbackController(detector, registry)
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Configure detector
        detector.detect_regression.return_value = Mock(
            is_regression=False,
            p_value=0.8
        )
        
        # Extended monitoring with varying data sizes
        memory_measurements = []
        
        for iteration in range(100):
            # Create variable-sized test data
            data_size = 10 + (iteration % 50)  # 10-60 data points
            
            historical_data = [
                Mock(metric_name="accuracy", value=0.85)
                for _ in range(data_size)
            ]
            current_data = [
                Mock(metric_name="accuracy", value=0.84)
                for _ in range(data_size // 2)
            ]
            
            # Perform health check
            health = controller.check_health(historical_data, current_data)
            assert health is not None
            
            # Measure memory every 10 iterations
            if iteration % 10 == 0:
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                memory_measurements.append(memory_increase)
                
                # Force cleanup
                del historical_data, current_data
                gc.collect()
        
        # Memory should not grow excessively
        final_memory_increase = memory_measurements[-1]
        assert final_memory_increase < 50 * 1024 * 1024,  f"Excessive memory usage: {final_memory_increase} bytes"

    def test_monitoring_under_regression_storm(self, monitoring_components):
        """Test monitoring performance during regression storm (many regressions)."""
        detector, registry = monitoring_components
        controller = RollbackController(detector, registry)
        
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Configure detector to always detect regression
        detector.detect_regression.return_value = Mock(
            is_regression=True,
            is_significant_change=True,
            p_value=0.001
        )
        
        historical_data = [Mock(metric_name="accuracy")]
        current_data = [Mock(metric_name="accuracy")]
        
        # Simulate regression storm
        regression_responses = []
        storm_start = time.time()
        
        for _ in range(50):  # 50 consecutive regressions
            start_time = time.time()
            
            # Check for automatic rollback
            rollback_result = controller.trigger_automatic_rollback_if_needed(
                historical_data, current_data
            )
            
            response_time = time.time() - start_time
            regression_responses.append(response_time)
            
            # First detection should trigger rollback
            if len(regression_responses) == 1:
                assert rollback_result is not None
                assert rollback_result.success is True
            else:
                # Subsequent detections should not trigger additional rollbacks
                assert rollback_result is None or not rollback_result.success
        
        storm_duration = time.time() - storm_start
        
        # Performance under regression storm
        max_response_time = max(regression_responses)
        avg_response_time = sum(regression_responses) / len(regression_responses)
        
        assert max_response_time < 5.0,  f"Slowest regression response: {max_response_time:.3f}s"
        assert avg_response_time < 1.0,  f"Average regression response: {avg_response_time:.3f}s"
        assert storm_duration < 60.0,    "Regression storm handling took too long"


class TestRollbackControllerConcurrencyAndThreadSafety:
    """Test concurrent operations and thread safety."""

    def test_concurrent_health_checks_thread_safety(self):
        """Test thread safety of concurrent health checks."""
        detector = Mock()
        registry = Mock()
        registry.rollback_to_model.return_value = Mock(success=True)
        
        controller = RollbackController(detector, registry)
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Configure detector
        detector.detect_regression.return_value = Mock(
            is_regression=False,
            p_value=0.8
        )
        
        results = []
        errors = []
        
        def health_check_worker(worker_id):
            worker_results = []
            try:
                for i in range(20):
                    historical_data = [Mock(metric_name="accuracy")]
                    current_data = [Mock(metric_name="accuracy")]
                    
                    health = controller.check_health(historical_data, current_data)
                    worker_results.append({
                        "worker_id": worker_id,
                        "check_id": i,
                        "is_healthy": health.is_healthy,
                        "timestamp": health.timestamp
                    })
                    
                    time.sleep(0.001)  # Small delay
                    
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")
            
            return worker_results
        
        # Run concurrent health checks
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(health_check_worker, i)
                for i in range(10)
            ]
            
            for future in as_completed(futures):
                results.extend(future.result())
        
        # Verify thread safety
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 200  # 10 workers × 20 checks each
        assert all(result["is_healthy"] is True for result in results)

    def test_concurrent_rollback_prevention(self):
        """Test prevention of concurrent rollback executions."""
        detector = Mock()
        registry = Mock()
        
        # Mock slow rollback to create race condition opportunity
        def slow_rollback(model_version):
            time.sleep(1)  # 1 second delay
            return Mock(success=True)
        
        registry.rollback_to_model.side_effect = slow_rollback
        
        controller = RollbackController(detector, registry)
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        rollback_results = []
        
        def rollback_worker(worker_id):
            try:
                result = controller.execute_manual_rollback(f"Concurrent rollback {worker_id}")
                rollback_results.append({
                    "worker_id": worker_id,
                    "success": result.success,
                    "duration": result.duration
                })
            except Exception as e:
                rollback_results.append({
                    "worker_id": worker_id,
                    "success": False,
                    "error": str(e)
                })
        
        # Start multiple rollbacks concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=rollback_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Only one rollback should succeed
        successful_rollbacks = [r for r in rollback_results if r["success"]]
        failed_rollbacks = [r for r in rollback_results if not r["success"]]
        
        assert len(successful_rollbacks) == 1, "Only one rollback should succeed"
        assert len(failed_rollbacks) == 4, "Other rollbacks should be prevented"
        
        # Registry should only be called once
        registry.rollback_to_model.assert_called_once()

    def test_monitoring_state_consistency_under_load(self):
        """Test monitoring state consistency under concurrent load."""
        detector = Mock()
        registry = Mock()
        registry.rollback_to_model.return_value = Mock(success=True)
        
        controller = RollbackController(detector, registry)
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Configure detector for mixed responses
        def variable_detector(*args, **kwargs):
            import random
            return Mock(
                is_regression=random.choice([True, False]),
                p_value=random.uniform(0.001, 0.9)
            )
        
        detector.detect_regression.side_effect = variable_detector
        
        operation_results = []
        
        def mixed_operations_worker(worker_id):
            worker_results = []
            
            for operation_id in range(10):
                try:
                    historical_data = [Mock(metric_name="accuracy")]
                    current_data = [Mock(metric_name="accuracy")]
                    
                    if operation_id % 3 == 0:
                        # Health check
                        health = controller.check_health(historical_data, current_data)
                        worker_results.append(("health", health.is_healthy))
                    elif operation_id % 3 == 1:
                        # Status check
                        status = controller.get_rollback_status()
                        worker_results.append(("status", status.is_monitoring))
                    else:
                        # Automatic rollback check
                        rollback = controller.trigger_automatic_rollback_if_needed(
                            historical_data, current_data
                        )
                        worker_results.append(("rollback", rollback is not None))
                    
                except Exception as e:
                    worker_results.append(("error", str(e)))
            
            return worker_results
        
        # Run mixed operations concurrently
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(mixed_operations_worker, i)
                for i in range(8)
            ]
            
            for future in as_completed(futures):
                operation_results.extend(future.result())
        
        # Verify state consistency
        final_status = controller.get_rollback_status()
        
        # Should still be monitoring
        assert final_status.is_monitoring is True
        assert final_status.current_model == "model_v2.0"
        assert final_status.fallback_model == "model_v1.9"
        
        # No errors should occur
        errors = [result for result in operation_results if result[0] == "error"]
        assert len(errors) == 0, f"State consistency errors: {errors}"


class TestRollbackControllerRealWorldPerformanceScenarios:
    """Test real-world production performance scenarios."""

    def test_microservice_mesh_rollback_performance(self):
        """Test rollback performance in microservice mesh scenario."""
        # Simulate multiple service dependencies
        services = ["user-service", "order-service", "payment-service", "notification-service"]
        
        rollback_times = {}
        
        for service in services:
            detector = Mock()
            detector.detect_regression.return_value = Mock(
                is_regression=True,
                p_value=0.001
            )
            
            registry = Mock()
            registry.rollback_to_model.return_value = Mock(success=True)
            
            controller = RollbackController(detector, registry)
            controller.start_monitoring(f"{service}_v2.0", f"{service}_v1.9")
            
            # Measure service-specific rollback time
            start_time = time.time()
            result = controller.execute_manual_rollback(f"Rollback {service} due to mesh issues")
            rollback_time = time.time() - start_time
            rollback_times[service] = rollback_time
            
            assert result.success is True
            assert rollback_time < 30.0  # Each service must meet SLA
        
        # Mesh-wide performance requirements
        total_rollback_time = sum(rollback_times.values())
        max_service_rollback = max(rollback_times.values())
        
        assert max_service_rollback < 15.0,  "Individual service rollback should be fast"
        assert total_rollback_time < 60.0,   "Total mesh rollback should be reasonable"

    def test_high_traffic_production_scenario(self):
        """Test rollback performance under high traffic conditions."""
        detector = Mock()
        registry = Mock()
        registry.rollback_to_model.return_value = Mock(success=True)
        
        controller = RollbackController(detector, registry)
        controller.start_monitoring("model_v2.0", "model_v1.9")
        
        # Simulate high traffic with many performance data points
        def generate_high_traffic_data(is_degraded=False):
            base_latency = 200 if is_degraded else 50  # ms
            return [
                Mock(
                    metric_name="response_latency_ms",
                    value=base_latency + (i % 20),  # Varying latency
                    timestamp=datetime.now() - timedelta(seconds=i),
                    metadata={"request_id": f"req_{i}", "traffic": "high"}
                )
                for i in range(1000)  # 1000 data points (high traffic)
            ]
        
        historical_data = generate_high_traffic_data(is_degraded=False)
        current_data = generate_high_traffic_data(is_degraded=True)
        
        # Configure detector to detect regression in high-traffic scenario
        detector.detect_regression.return_value = Mock(
            is_regression=True,
            is_significant_change=True,
            p_value=0.001,
            effect_size=2.5
        )
        
        # Measure rollback under high traffic
        start_time = time.time()
        rollback_result = controller.trigger_automatic_rollback_if_needed(
            historical_data, current_data
        )
        rollback_time = time.time() - start_time
        
        # High traffic rollback requirements
        assert rollback_result is not None
        assert rollback_result.success is True
        assert rollback_time < 30.0,  f"High traffic rollback took {rollback_time:.2f}s"
        assert rollback_result.trigger == RollbackTrigger.PERFORMANCE_REGRESSION

    def test_multi_region_rollback_simulation(self):
        """Test rollback performance in multi-region deployment."""
        regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
        
        region_rollback_times = {}
        
        for region in regions:
            detector = Mock()
            registry = Mock()
            
            # Simulate region-specific latency
            region_latency = {
                "us-east-1": 0.1,
                "us-west-2": 0.2,
                "eu-west-1": 0.15,
                "ap-southeast-1": 0.3
            }
            
            def region_specific_rollback(model_version):
                time.sleep(region_latency[region])  # Simulate network latency
                return Mock(success=True)
            
            registry.rollback_to_model.side_effect = region_specific_rollback
            detector.detect_regression.return_value = Mock(is_regression=True)
            
            controller = RollbackController(detector, registry)
            controller.start_monitoring(f"model_v2.0_{region}", f"model_v1.9_{region}")
            
            # Measure region-specific rollback
            start_time = time.time()
            result = controller.execute_manual_rollback(f"Multi-region rollback in {region}")
            rollback_time = time.time() - start_time
            region_rollback_times[region] = rollback_time
            
            assert result.success is True
            assert rollback_time < 30.0  # Each region must meet SLA
        
        # Multi-region performance analysis
        fastest_region = min(region_rollback_times.values())
        slowest_region = max(region_rollback_times.values())
        avg_rollback_time = sum(region_rollback_times.values()) / len(region_rollback_times)
        
        assert fastest_region >= 0.1,   "Should reflect minimum network latency"
        assert slowest_region < 5.0,    "Even slowest region should be fast"
        assert avg_rollback_time < 2.0, "Average across regions should be fast"

    def test_database_failover_rollback_scenario(self):
        """Test rollback performance during database failover."""
        detector = Mock()
        registry = Mock()
        
        # Simulate database failover scenario
        failover_stages = ["primary_down", "failover_in_progress", "secondary_active"]
        rollback_times_during_failover = {}
        
        for stage in failover_stages:
            # Configure registry behavior for each failover stage
            if stage == "primary_down":
                registry.rollback_to_model.side_effect = ConnectionError("Primary DB unavailable")
            elif stage == "failover_in_progress":
                def slow_failover_rollback(model_version):
                    time.sleep(10)  # Slow during failover
                    return Mock(success=True)
                registry.rollback_to_model.side_effect = slow_failover_rollback
            else:  # secondary_active
                registry.rollback_to_model.side_effect = lambda mv: Mock(success=True)
            
            controller = RollbackController(detector, registry)
            controller.start_monitoring("model_v2.0", "model_v1.9")
            
            start_time = time.time()
            try:
                result = controller.execute_manual_rollback(f"Rollback during {stage}")
                rollback_time = time.time() - start_time
                rollback_times_during_failover[stage] = {
                    "time": rollback_time,
                    "success": result.success
                }
            except Exception as e:
                rollback_time = time.time() - start_time
                rollback_times_during_failover[stage] = {
                    "time": rollback_time,
                    "success": False,
                    "error": str(e)
                }
        
        # Failover scenario analysis
        primary_down_result = rollback_times_during_failover["primary_down"]
        failover_progress_result = rollback_times_during_failover["failover_in_progress"]
        secondary_active_result = rollback_times_during_failover["secondary_active"]
        
        # Primary down should fail quickly
        assert primary_down_result["success"] is False
        assert primary_down_result["time"] < 5.0
        
        # Failover in progress should still meet SLA (though slower)
        assert failover_progress_result["success"] is True
        assert failover_progress_result["time"] < 30.0
        
        # Secondary active should be fast
        assert secondary_active_result["success"] is True
        assert secondary_active_result["time"] < 5.0


@pytest.mark.performance
class TestRollbackControllerStressAndLoadTesting:
    """Stress testing and load testing scenarios."""

    def test_rollback_under_extreme_load(self):
        """Test rollback performance under extreme system load."""
        detector = Mock()
        registry = Mock()
        registry.rollback_to_model.return_value = Mock(success=True)
        
        # Create extreme load conditions
        load_threads = []
        
        def cpu_intensive_background_load():
            """Create CPU load in background."""
            end_time = time.time() + 30
            while time.time() < end_time:
                _ = sum(i * i for i in range(10000))
        
        # Start background load
        for _ in range(4):  # 4 CPU-intensive threads
            thread = threading.Thread(target=cpu_intensive_background_load)
            load_threads.append(thread)
            thread.start()
        
        try:
            controller = RollbackController(detector, registry)
            controller.start_monitoring("model_v2.0", "model_v1.9")
            
            # Execute rollback under extreme load
            start_time = time.time()
            result = controller.execute_manual_rollback("Rollback under extreme load")
            rollback_time = time.time() - start_time
            
            # Should still meet SLA under extreme load
            assert result.success is True
            assert rollback_time < 30.0, f"Rollback under load took {rollback_time:.2f}s"
            
        finally:
            # Clean up background load
            for thread in load_threads:
                thread.join(timeout=1)

    def test_memory_leak_detection_during_extended_operation(self):
        """Test for memory leaks during extended rollback operations."""
        detector = Mock()
        registry = Mock()
        registry.rollback_to_model.return_value = Mock(success=True)
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Extended operations
        for cycle in range(50):
            controller = RollbackController(detector, registry)
            controller.start_monitoring(f"model_v2.{cycle}", f"model_v1.{cycle}")
            
            # Perform multiple rollbacks per cycle
            for rollback_id in range(5):
                result = controller.execute_manual_rollback(f"Cycle {cycle} rollback {rollback_id}")
                assert result.success is True
                
                # Reset for next rollback
                controller.stop_monitoring()
                controller.start_monitoring(f"model_v2.{cycle}.{rollback_id+1}", f"model_v1.{cycle}")
            
            # Force cleanup
            del controller
            gc.collect()
            
            # Check memory every 10 cycles
            if cycle % 10 == 0:
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                
                # Memory should not grow excessively
                assert memory_increase < 100 * 1024 * 1024, f"Memory leak detected: {memory_increase} bytes after {cycle} cycles"

    def test_rollback_throughput_benchmark(self):
        """Benchmark rollback throughput under optimal conditions."""
        detector = Mock()
        registry = Mock()
        registry.rollback_to_model.return_value = Mock(success=True)
        
        # Measure rollback throughput
        num_rollbacks = 100
        rollback_times = []
        
        for i in range(num_rollbacks):
            controller = RollbackController(detector, registry)
            controller.start_monitoring(f"model_v2.{i}", f"model_v1.{i}")
            
            start_time = time.time()
            result = controller.execute_manual_rollback(f"Throughput test rollback {i}")
            rollback_time = time.time() - start_time
            rollback_times.append(rollback_time)
            
            assert result.success is True
        
        # Throughput analysis
        total_time = sum(rollback_times)
        avg_rollback_time = total_time / num_rollbacks
        rollbacks_per_second = num_rollbacks / total_time
        
        # Performance benchmarks
        assert avg_rollback_time < 1.0,    f"Average rollback time: {avg_rollback_time:.3f}s"
        assert rollbacks_per_second > 10,  f"Rollback throughput: {rollbacks_per_second:.1f}/sec"
        assert max(rollback_times) < 5.0,  f"Slowest rollback: {max(rollback_times):.3f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])