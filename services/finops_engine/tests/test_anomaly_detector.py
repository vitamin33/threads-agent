"""
Test suite for Intelligent Anomaly Detection system (CRA-241)

Following TDD methodology to implement:
1. Cost anomalies (target: <$0.02/post, alert if >25% above)
2. Viral coefficient drops (alert if <70% of baseline)
3. Pattern fatigue (alert if fatigue score >0.8)
4. Multiple severity levels: critical, warning, info
5. Confidence scores (0.0-1.0) for each anomaly
6. Process alerts with <60s SLA

Test-first approach:
- Write failing tests for each feature
- Implement minimal code to make tests pass
- Refactor while keeping tests green
"""

import pytest
import time


class TestAnomalyEventDataClass:
    """Test the AnomalyEvent dataclass structure."""

    def test_anomaly_event_dataclass_initialization(self):
        """Test that AnomalyEvent dataclass can be instantiated with required fields.

        This is our first failing test - the dataclass doesn't exist yet!
        """
        # This will fail because AnomalyEvent doesn't exist
        from services.finops_engine.anomaly_detector import AnomalyEvent

        # Test minimal required fields
        event = AnomalyEvent(
            metric_name="cost_per_post",
            current_value=0.025,
            baseline=0.020,
            severity="warning",
            confidence=0.85,
            context={"persona_id": "ai_jesus", "post_count": 100},
        )

        # Verify all fields are properly set
        assert event.metric_name == "cost_per_post"
        assert event.current_value == 0.025
        assert event.baseline == 0.020
        assert event.severity == "warning"
        assert event.confidence == 0.85
        assert event.context["persona_id"] == "ai_jesus"
        assert event.context["post_count"] == 100

    def test_anomaly_event_severity_levels(self):
        """Test that AnomalyEvent supports all required severity levels."""
        from services.finops_engine.anomaly_detector import AnomalyEvent

        # Test all severity levels
        severities = ["critical", "warning", "info"]

        for severity in severities:
            event = AnomalyEvent(
                metric_name="test_metric",
                current_value=1.0,
                baseline=0.5,
                severity=severity,
                confidence=0.9,
                context={},
            )
            assert event.severity == severity

    def test_anomaly_event_confidence_bounds(self):
        """Test that confidence scores are bounded between 0.0 and 1.0."""
        from services.finops_engine.anomaly_detector import AnomalyEvent

        # Test valid confidence scores
        valid_confidences = [0.0, 0.5, 0.85, 1.0]

        for confidence in valid_confidences:
            event = AnomalyEvent(
                metric_name="test_metric",
                current_value=1.0,
                baseline=0.5,
                severity="warning",
                confidence=confidence,
                context={},
            )
            assert event.confidence == confidence
            assert 0.0 <= event.confidence <= 1.0


class TestAnomalyDetectorBasic:
    """Test basic AnomalyDetector instantiation and configuration."""

    def test_anomaly_detector_initialization(self):
        """Test that AnomalyDetector can be instantiated with default config.

        This will fail because AnomalyDetector class doesn't exist yet!
        """
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Basic assertions about the detector structure
        assert detector is not None
        assert hasattr(detector, "detect_cost_anomaly")
        assert hasattr(detector, "detect_viral_coefficient_drop")
        assert hasattr(detector, "detect_pattern_fatigue")

    def test_anomaly_detector_with_custom_config(self):
        """Test AnomalyDetector with custom configuration."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        config = {
            "cost_threshold": 0.02,
            "cost_alert_percent": 25,
            "viral_coefficient_threshold": 70,
            "pattern_fatigue_threshold": 0.8,
            "sla_seconds": 60,
        }

        detector = AnomalyDetector(config=config)

        assert detector.config == config
        assert detector.config["cost_threshold"] == 0.02
        assert detector.config["cost_alert_percent"] == 25


class TestCostAnomalyDetection:
    """Test cost anomaly detection: target <$0.02/post, alert if >25% above."""

    def test_detect_cost_anomaly_normal_case(self):
        """Test cost anomaly detection when costs are normal (under threshold)."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Normal cost case: $0.018/post (under $0.02 threshold)
        result = detector.detect_cost_anomaly(
            current_cost=0.018, baseline_cost=0.017, persona_id="ai_jesus"
        )

        # Should not detect anomaly
        assert result is None  # No anomaly detected

    def test_detect_cost_anomaly_25_percent_above_threshold(self):
        """Test cost anomaly detection when cost is exactly 25% above baseline."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Cost exactly 25% above threshold: $0.025/post (25% above $0.02)
        result = detector.detect_cost_anomaly(
            current_cost=0.025, baseline_cost=0.020, persona_id="ai_jesus"
        )

        # Should detect warning anomaly
        assert result is not None
        assert result.metric_name == "cost_per_post"
        assert result.current_value == 0.025
        assert result.baseline == 0.020
        assert result.severity == "warning"
        assert result.confidence >= 0.7  # Should have reasonable confidence
        assert result.context["persona_id"] == "ai_jesus"

    def test_detect_cost_anomaly_critical_threshold(self):
        """Test cost anomaly detection for critical cost spikes."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Critical cost spike: $0.040/post (100% above $0.02 threshold)
        result = detector.detect_cost_anomaly(
            current_cost=0.040, baseline_cost=0.020, persona_id="ai_jesus"
        )

        # Should detect critical anomaly
        assert result is not None
        assert result.severity == "critical"
        assert result.confidence >= 0.9  # High confidence for clear spike
        assert result.current_value == 0.040


class TestViralCoefficientDetection:
    """Test viral coefficient drop detection: alert if <70% of baseline."""

    def test_detect_viral_coefficient_normal_case(self):
        """Test viral coefficient detection when performance is normal."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Normal case: current 85% of baseline (above 70% threshold)
        result = detector.detect_viral_coefficient_drop(
            current_coefficient=0.85, baseline_coefficient=1.0, persona_id="ai_jesus"
        )

        # Should not detect anomaly
        assert result is None

    def test_detect_viral_coefficient_exactly_70_percent(self):
        """Test viral coefficient detection at exactly 70% threshold."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Exactly at threshold: current is 70% of baseline
        result = detector.detect_viral_coefficient_drop(
            current_coefficient=0.70, baseline_coefficient=1.0, persona_id="ai_jesus"
        )

        # Should detect warning anomaly (at threshold)
        assert result is not None
        assert result.metric_name == "viral_coefficient"
        assert result.severity == "warning"
        assert result.confidence >= 0.6

    def test_detect_viral_coefficient_critical_drop(self):
        """Test viral coefficient detection for severe drops."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Critical drop: current is 40% of baseline
        result = detector.detect_viral_coefficient_drop(
            current_coefficient=0.40, baseline_coefficient=1.0, persona_id="ai_jesus"
        )

        # Should detect critical anomaly
        assert result is not None
        assert result.severity == "critical"
        assert result.confidence >= 0.8
        assert result.current_value == 0.40
        assert result.baseline == 1.0


class TestPatternFatigueDetection:
    """Test pattern fatigue detection: alert if fatigue score >0.8."""

    def test_detect_pattern_fatigue_normal_case(self):
        """Test pattern fatigue detection when fatigue is normal."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Normal case: fatigue score 0.6 (under 0.8 threshold)
        result = detector.detect_pattern_fatigue(
            fatigue_score=0.6, persona_id="ai_jesus"
        )

        # Should not detect anomaly
        assert result is None

    def test_detect_pattern_fatigue_at_threshold(self):
        """Test pattern fatigue detection at exactly 0.8 threshold."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # At threshold: fatigue score 0.8
        result = detector.detect_pattern_fatigue(
            fatigue_score=0.8, persona_id="ai_jesus"
        )

        # Should detect warning anomaly
        assert result is not None
        assert result.metric_name == "pattern_fatigue"
        assert result.current_value == 0.8
        assert result.severity == "warning"
        assert result.confidence >= 0.7

    def test_detect_pattern_fatigue_critical_level(self):
        """Test pattern fatigue detection for critical fatigue levels."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Critical fatigue: score 0.95
        result = detector.detect_pattern_fatigue(
            fatigue_score=0.95, persona_id="ai_jesus"
        )

        # Should detect critical anomaly
        assert result is not None
        assert result.severity == "critical"
        assert result.confidence >= 0.9
        assert result.current_value == 0.95


class TestPerformanceSLA:
    """Test that anomaly detection meets <60s SLA requirement."""

    @pytest.mark.asyncio
    async def test_anomaly_detection_performance_sla(self):
        """Test that anomaly detection completes within 60 seconds SLA."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Measure time for multiple anomaly detections
        start_time = time.time()

        # Run all three detection types
        cost_result = detector.detect_cost_anomaly(
            current_cost=0.030, baseline_cost=0.020, persona_id="ai_jesus"
        )

        viral_result = detector.detect_viral_coefficient_drop(
            current_coefficient=0.65, baseline_coefficient=1.0, persona_id="ai_jesus"
        )

        fatigue_result = detector.detect_pattern_fatigue(
            fatigue_score=0.85, persona_id="ai_jesus"
        )

        end_time = time.time()
        duration = end_time - start_time

        # Verify SLA compliance
        assert duration < 60.0, f"Detection took {duration:.2f}s, exceeds 60s SLA"

        # Verify all detections worked
        assert cost_result is not None  # Should detect cost anomaly
        assert viral_result is not None  # Should detect viral drop
        assert fatigue_result is not None  # Should detect pattern fatigue


class TestAnomalyDetectorEdgeCases:
    """Test edge cases and error handling for AnomalyDetector."""

    def test_detect_cost_anomaly_zero_baseline(self):
        """Test cost anomaly detection with zero baseline cost."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Zero baseline case
        result = detector.detect_cost_anomaly(
            current_cost=0.025, baseline_cost=0.0, persona_id="ai_jesus"
        )

        # Should detect anomaly since current_cost > threshold
        assert result is not None
        assert result.severity == "warning"
        assert result.current_value == 0.025

    def test_detect_cost_anomaly_negative_values(self):
        """Test cost anomaly detection with negative values (edge case)."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Negative baseline should not cause issues
        result = detector.detect_cost_anomaly(
            current_cost=-0.01, baseline_cost=-0.02, persona_id="ai_jesus"
        )

        # Should not detect anomaly for negative costs
        assert result is None

    def test_detect_viral_coefficient_zero_baseline(self):
        """Test viral coefficient detection with zero baseline."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Zero baseline case
        result = detector.detect_viral_coefficient_drop(
            current_coefficient=0.5, baseline_coefficient=0.0, persona_id="ai_jesus"
        )

        # Should not detect anomaly with zero baseline
        assert result is None

    def test_detect_pattern_fatigue_boundary_values(self):
        """Test pattern fatigue detection at boundary values."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Just below threshold
        result1 = detector.detect_pattern_fatigue(
            fatigue_score=0.79, persona_id="ai_jesus"
        )
        assert result1 is None

        # Exactly at threshold
        result2 = detector.detect_pattern_fatigue(
            fatigue_score=0.8, persona_id="ai_jesus"
        )
        assert result2 is not None
        assert result2.severity == "warning"

    def test_confidence_scores_within_bounds(self):
        """Test that all confidence scores are within 0.0-1.0 range."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Test various anomaly levels
        test_cases = [
            # (method, args, expected_min_confidence)
            ("detect_cost_anomaly", (0.040, 0.020, "ai_jesus"), 0.7),
            ("detect_viral_coefficient_drop", (0.40, 1.0, "ai_jesus"), 0.6),
            ("detect_pattern_fatigue", (0.95, "ai_jesus"), 0.7),
        ]

        for method_name, args, min_confidence in test_cases:
            method = getattr(detector, method_name)
            result = method(*args)

            assert result is not None
            assert 0.0 <= result.confidence <= 1.0
            assert result.confidence >= min_confidence

    def test_custom_configuration_overrides(self):
        """Test that custom configuration properly overrides defaults."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        custom_config = {
            "cost_threshold": 0.01,  # Lower threshold
            "cost_alert_percent": 10,  # Lower alert percentage
            "viral_coefficient_threshold": 80,  # Higher threshold
            "pattern_fatigue_threshold": 0.9,  # Higher threshold
        }

        detector = AnomalyDetector(config=custom_config)

        # Test cost anomaly with custom threshold
        result = detector.detect_cost_anomaly(
            current_cost=0.011,  # Just above 0.01 threshold
            baseline_cost=0.010,
            persona_id="ai_jesus",
        )
        assert result is not None  # Should detect with lower threshold

        # Test viral coefficient with custom threshold
        result2 = detector.detect_viral_coefficient_drop(
            current_coefficient=0.75,  # 75% of baseline
            baseline_coefficient=1.0,
            persona_id="ai_jesus",
        )
        assert result2 is not None  # Should detect with 80% threshold

        # Test pattern fatigue with custom threshold
        result3 = detector.detect_pattern_fatigue(
            fatigue_score=0.85,  # Below 0.9 threshold
            persona_id="ai_jesus",
        )
        assert result3 is None  # Should not detect with higher threshold


class TestAnomalyDetectorIntegration:
    """Integration tests showing complete anomaly detection workflow."""

    def test_multiple_anomaly_detection_workflow(self):
        """Test detecting multiple types of anomalies in a single workflow."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Simulate a scenario with multiple anomalies
        anomalies = []

        # 1. Cost anomaly: High cost per post
        cost_anomaly = detector.detect_cost_anomaly(
            current_cost=0.035,  # Above $0.02 threshold
            baseline_cost=0.020,
            persona_id="ai_jesus",
        )
        if cost_anomaly:
            anomalies.append(cost_anomaly)

        # 2. Viral coefficient drop: Poor performance
        viral_anomaly = detector.detect_viral_coefficient_drop(
            current_coefficient=0.60,  # Below 70% threshold
            baseline_coefficient=1.0,
            persona_id="ai_jesus",
        )
        if viral_anomaly:
            anomalies.append(viral_anomaly)

        # 3. Pattern fatigue: Content getting stale
        fatigue_anomaly = detector.detect_pattern_fatigue(
            fatigue_score=0.85,  # Above 0.8 threshold
            persona_id="ai_jesus",
        )
        if fatigue_anomaly:
            anomalies.append(fatigue_anomaly)

        # Verify all anomalies were detected
        assert len(anomalies) == 3

        # Verify each anomaly has proper structure
        for anomaly in anomalies:
            assert hasattr(anomaly, "metric_name")
            assert hasattr(anomaly, "current_value")
            assert hasattr(anomaly, "baseline")
            assert hasattr(anomaly, "severity")
            assert hasattr(anomaly, "confidence")
            assert hasattr(anomaly, "context")
            assert anomaly.confidence >= 0.0
            assert anomaly.confidence <= 1.0
            assert anomaly.severity in ["critical", "warning", "info"]
            assert "persona_id" in anomaly.context

    def test_no_anomalies_detected_normal_operation(self):
        """Test that no anomalies are detected during normal operation."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Normal operation: all metrics within acceptable ranges
        cost_result = detector.detect_cost_anomaly(
            current_cost=0.018,  # Under $0.02 threshold
            baseline_cost=0.017,
            persona_id="ai_jesus",
        )

        viral_result = detector.detect_viral_coefficient_drop(
            current_coefficient=0.85,  # Above 70% threshold
            baseline_coefficient=1.0,
            persona_id="ai_jesus",
        )

        fatigue_result = detector.detect_pattern_fatigue(
            fatigue_score=0.6,  # Below 0.8 threshold
            persona_id="ai_jesus",
        )

        # No anomalies should be detected
        assert cost_result is None
        assert viral_result is None
        assert fatigue_result is None

    def test_anomaly_severity_escalation(self):
        """Test that anomaly severity escalates correctly with increasing problems."""
        from services.finops_engine.anomaly_detector import AnomalyDetector

        detector = AnomalyDetector()

        # Test cost anomaly severity escalation
        minor_cost = detector.detect_cost_anomaly(
            0.025, 0.020, "ai_jesus"
        )  # 25% increase
        major_cost = detector.detect_cost_anomaly(
            0.040, 0.020, "ai_jesus"
        )  # 100% increase

        assert minor_cost.severity == "warning"
        assert major_cost.severity == "critical"
        assert major_cost.confidence > minor_cost.confidence

        # Test viral coefficient severity escalation
        minor_viral = detector.detect_viral_coefficient_drop(
            0.65, 1.0, "ai_jesus"
        )  # 65%
        major_viral = detector.detect_viral_coefficient_drop(
            0.35, 1.0, "ai_jesus"
        )  # 35%

        assert minor_viral.severity == "warning"
        assert major_viral.severity == "critical"
        assert major_viral.confidence > minor_viral.confidence
