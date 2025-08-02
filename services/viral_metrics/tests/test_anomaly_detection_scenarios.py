"""
Anomaly detection scenario tests for viral metrics system.

Tests various edge cases and scenarios for detecting performance
anomalies in viral content metrics.
"""

import pytest
from unittest.mock import patch

from services.viral_metrics.background_processor import ViralMetricsProcessor


class TestAnomalyDetectionScenarios:
    """Test suite for anomaly detection in viral metrics."""

    @pytest.mark.e2e
    async def test_viral_coefficient_drop_detection(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test detection of significant viral coefficient drops."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Test scenarios with different drop percentages
            scenarios = [
                {
                    "name": "minor_drop",
                    "baseline": {"viral_coefficient": 0.10},
                    "current": {"viral_coefficient": 0.08},
                    "expected_severity": None,  # Should not trigger (20% drop)
                },
                {
                    "name": "medium_drop",
                    "baseline": {"viral_coefficient": 0.10},
                    "current": {"viral_coefficient": 0.06},
                    "expected_severity": "medium",  # 40% drop
                },
                {
                    "name": "severe_drop",
                    "baseline": {"viral_coefficient": 0.10},
                    "current": {"viral_coefficient": 0.04},
                    "expected_severity": "high",  # 60% drop
                },
            ]

            for scenario in scenarios:
                with patch.object(
                    processor.metrics_collector,
                    "get_baseline_metrics",
                    return_value=scenario["baseline"],
                ):
                    anomalies = await processor.check_metrics_anomalies(
                        f"drop_test_{scenario['name']}", scenario["current"]
                    )

                    vc_anomalies = [
                        a for a in anomalies if a["type"] == "viral_coefficient_drop"
                    ]

                    if scenario["expected_severity"]:
                        assert len(vc_anomalies) == 1, (
                            f"Should detect viral coefficient drop for {scenario['name']}"
                        )
                        anomaly = vc_anomalies[0]
                        assert anomaly["severity"] == scenario["expected_severity"]
                        assert anomaly["drop_percentage"] > 0.3  # Above 30% threshold
                        assert "baseline_value" in anomaly
                        assert "current_value" in anomaly
                    else:
                        assert len(vc_anomalies) == 0, (
                            f"Should not detect minor drop for {scenario['name']}"
                        )

    @pytest.mark.e2e
    async def test_engagement_trajectory_anomalies(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test detection of negative engagement trajectory anomalies."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Test different trajectory scenarios
            trajectory_scenarios = [
                {"name": "slight_decline", "trajectory": -20, "should_trigger": False},
                {
                    "name": "significant_decline",
                    "trajectory": -60,
                    "should_trigger": True,
                },
                {"name": "rapid_decline", "trajectory": -85, "should_trigger": True},
                {
                    "name": "positive_trajectory",
                    "trajectory": 45,
                    "should_trigger": False,
                },
            ]

            for scenario in trajectory_scenarios:
                current_metrics = {"engagement_trajectory": scenario["trajectory"]}

                anomalies = await processor.check_metrics_anomalies(
                    f"trajectory_test_{scenario['name']}", current_metrics
                )
                trajectory_anomalies = [
                    a for a in anomalies if a["type"] == "negative_trajectory"
                ]

                if scenario["should_trigger"]:
                    assert len(trajectory_anomalies) == 1, (
                        f"Should detect negative trajectory for {scenario['name']}"
                    )
                    anomaly = trajectory_anomalies[0]
                    assert anomaly["severity"] == "medium"
                    assert anomaly["trajectory_value"] == scenario["trajectory"]
                    assert "rapidly decelerating" in anomaly["message"]
                else:
                    assert len(trajectory_anomalies) == 0, (
                        f"Should not detect trajectory anomaly for {scenario['name']}"
                    )

    @pytest.mark.e2e
    async def test_pattern_fatigue_detection(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test detection of content pattern fatigue."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Test different fatigue levels
            fatigue_scenarios = [
                {
                    "name": "fresh_pattern",
                    "fatigue_score": 0.2,
                    "should_trigger": False,
                },
                {
                    "name": "moderate_fatigue",
                    "fatigue_score": 0.65,
                    "should_trigger": False,
                },
                {"name": "high_fatigue", "fatigue_score": 0.85, "should_trigger": True},
                {
                    "name": "extreme_fatigue",
                    "fatigue_score": 0.95,
                    "should_trigger": True,
                },
            ]

            for scenario in fatigue_scenarios:
                current_metrics = {"pattern_fatigue": scenario["fatigue_score"]}

                anomalies = await processor.check_metrics_anomalies(
                    f"fatigue_test_{scenario['name']}", current_metrics
                )
                fatigue_anomalies = [
                    a for a in anomalies if a["type"] == "pattern_fatigue"
                ]

                if scenario["should_trigger"]:
                    assert len(fatigue_anomalies) == 1, (
                        f"Should detect pattern fatigue for {scenario['name']}"
                    )
                    anomaly = fatigue_anomalies[0]
                    assert (
                        anomaly["severity"] == "low"
                    )  # Pattern fatigue is low priority
                    assert anomaly["fatigue_score"] == scenario["fatigue_score"]
                    assert "pattern showing high fatigue" in anomaly["message"]
                else:
                    assert len(fatigue_anomalies) == 0, (
                        f"Should not detect fatigue for {scenario['name']}"
                    )

    @pytest.mark.e2e
    async def test_multiple_simultaneous_anomalies(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test detection when multiple anomalies occur simultaneously."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Create scenario with multiple anomalies
            baseline_metrics = {
                "viral_coefficient": 0.08,
                "scroll_stop_rate": 0.70,
                "share_velocity": 25.0,
            }

            current_metrics = {
                "viral_coefficient": 0.04,  # 50% drop - should trigger high severity
                "engagement_trajectory": -75,  # Rapid decline - should trigger medium severity
                "pattern_fatigue": 0.90,  # High fatigue - should trigger low severity
            }

            with patch.object(
                processor.metrics_collector,
                "get_baseline_metrics",
                return_value=baseline_metrics,
            ):
                anomalies = await processor.check_metrics_anomalies(
                    "multi_anomaly_test", current_metrics
                )

                # Should detect all three anomalies
                anomaly_types = {a["type"] for a in anomalies}
                expected_types = {
                    "viral_coefficient_drop",
                    "negative_trajectory",
                    "pattern_fatigue",
                }
                assert anomaly_types == expected_types, (
                    f"Expected {expected_types}, got {anomaly_types}"
                )

                # Verify severity levels
                severities = {a["type"]: a["severity"] for a in anomalies}
                assert severities["viral_coefficient_drop"] == "high"
                assert severities["negative_trajectory"] == "medium"
                assert severities["pattern_fatigue"] == "low"

                # Should trigger alert for high-severity anomalies
                high_severity_anomalies = [
                    a for a in anomalies if a["severity"] == "high"
                ]
                assert len(high_severity_anomalies) == 1

    @pytest.mark.e2e
    async def test_anomaly_threshold_edge_cases(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test anomaly detection at threshold boundaries."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Test edge cases at exact thresholds
            edge_cases = [
                {
                    "name": "exactly_30_percent_drop",
                    "baseline": {"viral_coefficient": 0.10},
                    "current": {"viral_coefficient": 0.07},  # Exactly 30% drop
                    "should_trigger": True,  # Should trigger at threshold
                },
                {
                    "name": "just_under_threshold",
                    "baseline": {"viral_coefficient": 0.10},
                    "current": {"viral_coefficient": 0.0701},  # 29.9% drop
                    "should_trigger": False,  # Should not trigger just under threshold
                },
                {
                    "name": "trajectory_exactly_minus_50",
                    "current": {"engagement_trajectory": -50},
                    "should_trigger": True,  # Should trigger at threshold
                },
                {
                    "name": "trajectory_just_under_threshold",
                    "current": {"engagement_trajectory": -49},
                    "should_trigger": False,  # Should not trigger just under threshold
                },
                {
                    "name": "fatigue_exactly_0_8",
                    "current": {"pattern_fatigue": 0.8},
                    "should_trigger": False,  # Should not trigger at 0.8 (threshold is > 0.8)
                },
                {
                    "name": "fatigue_just_over_threshold",
                    "current": {"pattern_fatigue": 0.801},
                    "should_trigger": True,  # Should trigger just over threshold
                },
            ]

            for case in edge_cases:
                baseline = case.get("baseline", {})
                with patch.object(
                    processor.metrics_collector,
                    "get_baseline_metrics",
                    return_value=baseline,
                ):
                    anomalies = await processor.check_metrics_anomalies(
                        f"edge_case_{case['name']}", case["current"]
                    )

                    has_anomaly = len(anomalies) > 0
                    assert has_anomaly == case["should_trigger"], (
                        f"Edge case {case['name']}: expected trigger={case['should_trigger']}, got {has_anomaly}"
                    )

    @pytest.mark.e2e
    async def test_anomaly_detection_with_missing_baseline(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test anomaly detection behavior when baseline data is unavailable."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Test with no baseline data
            with patch.object(
                processor.metrics_collector, "get_baseline_metrics", return_value={}
            ):
                current_metrics = {
                    "viral_coefficient": 0.02,  # Very low, but no baseline to compare
                    "engagement_trajectory": -80,  # Still detectable without baseline
                    "pattern_fatigue": 0.9,  # Still detectable without baseline
                }

                anomalies = await processor.check_metrics_anomalies(
                    "no_baseline_test", current_metrics
                )

                # Should still detect trajectory and fatigue anomalies (don't need baseline)
                anomaly_types = {a["type"] for a in anomalies}

                # Should not detect viral coefficient drop (needs baseline)
                assert "viral_coefficient_drop" not in anomaly_types

                # Should detect other anomalies that don't require baseline
                assert "negative_trajectory" in anomaly_types
                assert "pattern_fatigue" in anomaly_types

    @pytest.mark.e2e
    async def test_anomaly_detection_performance(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test performance of anomaly detection under load."""
        import time

        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            baseline_metrics = {"viral_coefficient": 0.08, "scroll_stop_rate": 0.65}

            # Test anomaly detection for many posts
            detection_times = []

            for i in range(100):
                current_metrics = {
                    "viral_coefficient": 0.04 + (i % 10) * 0.001,  # Varying values
                    "engagement_trajectory": -60 + (i % 20),
                    "pattern_fatigue": 0.8 + (i % 10) * 0.01,
                }

                with patch.object(
                    processor.metrics_collector,
                    "get_baseline_metrics",
                    return_value=baseline_metrics,
                ):
                    start_time = time.time()
                    await processor.check_metrics_anomalies(
                        f"perf_test_{i}", current_metrics
                    )
                    end_time = time.time()

                    detection_time = end_time - start_time
                    detection_times.append(detection_time)

                    # Should complete quickly
                    assert detection_time < 0.1, (
                        f"Anomaly detection took {detection_time:.3f}s, expected < 0.1s"
                    )

            # Overall performance checks
            avg_time = sum(detection_times) / len(detection_times)
            max_time = max(detection_times)

            assert avg_time < 0.01, f"Average detection time {avg_time:.3f}s too high"
            assert max_time < 0.05, f"Max detection time {max_time:.3f}s too high"

    @pytest.mark.e2e
    async def test_anomaly_alert_triggering(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test that high-severity anomalies trigger alert system."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Mock the alert sending function
            alert_calls = []

            async def mock_send_alerts(post_id, anomalies):
                alert_calls.append({"post_id": post_id, "anomalies": anomalies})

            with patch.object(
                processor, "send_metrics_alerts", side_effect=mock_send_alerts
            ):
                baseline_metrics = {"viral_coefficient": 0.10}

                # Test scenarios with different severity levels
                test_scenarios = [
                    {
                        "name": "low_severity_only",
                        "metrics": {"pattern_fatigue": 0.9},
                        "should_alert": False,
                    },
                    {
                        "name": "medium_severity_only",
                        "metrics": {"engagement_trajectory": -70},
                        "should_alert": False,
                    },
                    {
                        "name": "high_severity",
                        "metrics": {"viral_coefficient": 0.04},  # 60% drop
                        "should_alert": True,
                    },
                    {
                        "name": "mixed_with_high",
                        "metrics": {
                            "viral_coefficient": 0.045,  # 55% drop - high severity
                            "pattern_fatigue": 0.85,  # low severity
                        },
                        "should_alert": True,
                    },
                ]

                for scenario in test_scenarios:
                    alert_calls.clear()  # Reset alert tracking

                    with patch.object(
                        processor.metrics_collector,
                        "get_baseline_metrics",
                        return_value=baseline_metrics,
                    ):
                        await processor.check_metrics_anomalies(
                            f"alert_test_{scenario['name']}", scenario["metrics"]
                        )

                        if scenario["should_alert"]:
                            assert len(alert_calls) == 1, (
                                f"Should trigger alert for {scenario['name']}"
                            )
                            alert_call = alert_calls[0]
                            assert (
                                alert_call["post_id"]
                                == f"alert_test_{scenario['name']}"
                            )
                            # Should only include high-severity anomalies in alert
                            high_severity_anomalies = [
                                a
                                for a in alert_call["anomalies"]
                                if a["severity"] == "high"
                            ]
                            assert len(high_severity_anomalies) > 0
                        else:
                            assert len(alert_calls) == 0, (
                                f"Should not trigger alert for {scenario['name']}"
                            )

    @pytest.mark.e2e
    async def test_anomaly_detection_data_validation(
        self, mock_redis, mock_database, mock_prometheus
    ):
        """Test anomaly detection with invalid or edge-case data."""
        with (
            patch(
                "services.viral_metrics.background_processor.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_redis_connection",
                return_value=mock_redis,
            ),
            patch(
                "services.viral_metrics.metrics_collector.get_db_connection",
                return_value=mock_database,
            ),
            patch(
                "services.viral_metrics.metrics_collector.PrometheusClient",
                return_value=mock_prometheus,
            ),
        ):
            processor = ViralMetricsProcessor()

            # Test with various invalid data scenarios
            invalid_data_scenarios = [
                {
                    "name": "negative_viral_coefficient",
                    "baseline": {"viral_coefficient": 0.08},
                    "current": {"viral_coefficient": -0.02},
                    "should_handle_gracefully": True,
                },
                {
                    "name": "zero_baseline",
                    "baseline": {"viral_coefficient": 0.0},
                    "current": {"viral_coefficient": 0.05},
                    "should_handle_gracefully": True,
                },
                {
                    "name": "extreme_trajectory",
                    "current": {"engagement_trajectory": -1000},
                    "should_handle_gracefully": True,
                },
                {
                    "name": "invalid_fatigue_score",
                    "current": {"pattern_fatigue": 1.5},  # > 1.0
                    "should_handle_gracefully": True,
                },
                {
                    "name": "missing_metrics",
                    "current": {},  # Empty metrics
                    "should_handle_gracefully": True,
                },
            ]

            for scenario in invalid_data_scenarios:
                baseline = scenario.get("baseline", {})

                try:
                    with patch.object(
                        processor.metrics_collector,
                        "get_baseline_metrics",
                        return_value=baseline,
                    ):
                        anomalies = await processor.check_metrics_anomalies(
                            f"invalid_data_{scenario['name']}", scenario["current"]
                        )

                        # Should not crash and should return a list
                        assert isinstance(anomalies, list), (
                            f"Should return list for {scenario['name']}"
                        )

                        # Anomalies should have valid structure if any are detected
                        for anomaly in anomalies:
                            assert "type" in anomaly
                            assert "severity" in anomaly
                            assert anomaly["severity"] in ["low", "medium", "high"]

                except Exception as e:
                    if scenario["should_handle_gracefully"]:
                        pytest.fail(
                            f"Should handle {scenario['name']} gracefully, but got: {e}"
                        )
                    # If we expect it to fail, that's okay
