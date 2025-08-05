"""
Test suite for Cost Anomaly Detection & Alerting System (CRA-240)

Following TDD methodology to implement:
- Statistical anomaly detection (3x baseline)
- Pattern-based detection
- ML-based detection
- Multi-channel alerting (Slack, PagerDuty, Email)
- Circuit breaker automated responses
- Sub-60 second response time

Target thresholds:
- Cost spikes: 3x normal baseline
- Efficiency drops: 30% decrease
- Negative ROI: -50%
- Budget overrun: 80% of budget
"""

import pytest
from datetime import datetime


class TestCostAnomalyDetector:
    """Test suite for CostAnomalyDetector with multiple detection algorithms."""

    def test_cost_anomaly_detector_initialization(self):
        """Test that CostAnomalyDetector can be instantiated with configuration.

        This is our first failing test - the class doesn't exist yet!
        """
        # This will fail because CostAnomalyDetector doesn't exist
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector

        config = {
            "baseline_lookback_hours": 24,  # 24 hours for baseline calculation
            "spike_threshold_multiplier": 3.0,  # 3x baseline = anomaly
            "efficiency_drop_threshold": 0.30,  # 30% efficiency drop
            "negative_roi_threshold": -0.50,  # -50% ROI
            "budget_overrun_threshold": 0.80,  # 80% of budget
            "response_time_target_seconds": 60,  # <60 second response
        }

        detector = CostAnomalyDetector(config=config)

        # Basic assertions about the detector structure
        assert detector is not None
        assert detector.config == config
        assert hasattr(detector, "detect_statistical_anomaly")
        assert hasattr(detector, "detect_pattern_anomaly")
        assert hasattr(detector, "detect_ml_anomaly")
        assert hasattr(detector, "calculate_baseline")

    def test_cost_anomaly_detector_statistical_detection_no_anomaly(self):
        """Test statistical anomaly detection when costs are normal (under 3x baseline)."""
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector

        detector = CostAnomalyDetector()

        # Historical baseline data (last 24 hours)
        baseline_costs = [0.015, 0.018, 0.020, 0.017, 0.019]  # Average ~0.018

        # Current cost within normal range (2x baseline)
        current_cost = 0.035  # 2x baseline = no anomaly

        anomaly_result = detector.detect_statistical_anomaly(
            current_cost=current_cost,
            baseline_costs=baseline_costs,
            persona_id="ai_jesus",
        )

        # Should not detect anomaly
        assert anomaly_result["is_anomaly"] is False
        assert anomaly_result["severity"] == "normal"
        assert anomaly_result["current_cost"] == current_cost
        assert "baseline_avg" in anomaly_result
        assert "multiplier" in anomaly_result

    def test_cost_anomaly_detector_statistical_detection_with_anomaly(self):
        """Test statistical anomaly detection when costs exceed 3x baseline."""
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector

        detector = CostAnomalyDetector()

        # Historical baseline data
        baseline_costs = [0.015, 0.018, 0.020, 0.017, 0.019]  # Average ~0.018

        # Current cost exceeds 3x baseline
        current_cost = 0.065  # 3.6x baseline = anomaly!

        anomaly_result = detector.detect_statistical_anomaly(
            current_cost=current_cost,
            baseline_costs=baseline_costs,
            persona_id="ai_jesus",
        )

        # Should detect anomaly
        assert anomaly_result["is_anomaly"] is True
        assert anomaly_result["severity"] == "high"
        assert anomaly_result["current_cost"] == current_cost
        assert anomaly_result["multiplier"] > 3.0
        assert anomaly_result["anomaly_type"] == "cost_spike"
        assert "baseline_avg" in anomaly_result

    def test_cost_anomaly_detector_efficiency_drop_detection(self):
        """Test detection of efficiency drops (30% decrease in posts per dollar)."""
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector

        detector = CostAnomalyDetector()

        # Historical efficiency data (posts per dollar)
        baseline_efficiency = [50.0, 52.0, 48.0, 51.0, 49.0]  # Average ~50 posts/$

        # Current efficiency shows 30%+ drop
        current_efficiency = 34.0  # 32% drop from ~50 = anomaly

        anomaly_result = detector.detect_efficiency_anomaly(
            current_efficiency=current_efficiency,
            baseline_efficiency=baseline_efficiency,
            persona_id="ai_jesus",
        )

        # Should detect efficiency anomaly
        assert anomaly_result["is_anomaly"] is True
        assert anomaly_result["severity"] == "medium"
        assert anomaly_result["anomaly_type"] == "efficiency_drop"
        assert anomaly_result["efficiency_drop_percent"] > 30.0

    def test_cost_anomaly_detector_negative_roi_detection(self):
        """Test detection of negative ROI (-50% threshold)."""
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector

        detector = CostAnomalyDetector()

        # ROI calculation data
        costs = 100.0  # $100 spent
        revenue = 45.0  # $45 earned = -55% ROI

        anomaly_result = detector.detect_roi_anomaly(
            costs=costs, revenue=revenue, persona_id="ai_jesus"
        )

        # Should detect negative ROI anomaly
        assert anomaly_result["is_anomaly"] is True
        assert anomaly_result["severity"] == "critical"
        assert anomaly_result["anomaly_type"] == "negative_roi"
        assert anomaly_result["roi_percent"] < -50.0

    def test_cost_anomaly_detector_budget_overrun_detection(self):
        """Test detection of budget overrun (80% threshold)."""
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector

        detector = CostAnomalyDetector()

        # Budget tracking data
        monthly_budget = 1000.0  # $1000 monthly budget
        current_spend = 850.0  # $850 spent = 85% of budget

        anomaly_result = detector.detect_budget_anomaly(
            current_spend=current_spend,
            budget_limit=monthly_budget,
            persona_id="ai_jesus",
        )

        # Should detect budget overrun anomaly
        assert anomaly_result["is_anomaly"] is True
        assert anomaly_result["severity"] == "high"
        assert anomaly_result["anomaly_type"] == "budget_overrun"
        assert anomaly_result["budget_usage_percent"] > 80.0


class TestAlertManager:
    """Test suite for AlertManager with multi-channel notifications."""

    def test_alert_manager_initialization(self):
        """Test that AlertManager can be instantiated with channel configurations.

        This will fail because AlertManager doesn't exist yet!
        """
        from services.finops_engine.alert_manager import AlertManager

        config = {
            "channels": {
                "slack": {
                    "webhook_url": "https://hooks.slack.com/test",
                    "channel": "#finops-alerts",
                    "enabled": True,
                },
                "pagerduty": {"integration_key": "test-key-123", "enabled": True},
                "email": {
                    "smtp_server": "smtp.gmail.com",
                    "recipients": ["team@company.com"],
                    "enabled": True,
                },
            },
            "severity_routing": {
                "critical": ["slack", "pagerduty", "email"],
                "high": ["slack", "pagerduty"],
                "medium": ["slack"],
                "low": ["email"],
            },
        }

        alert_manager = AlertManager(config=config)

        assert alert_manager is not None
        assert alert_manager.config == config
        assert hasattr(alert_manager, "send_alert")
        assert hasattr(alert_manager, "send_slack_alert")
        assert hasattr(alert_manager, "send_pagerduty_alert")
        assert hasattr(alert_manager, "send_email_alert")

    @pytest.mark.asyncio
    async def test_alert_manager_send_critical_alert_all_channels(self):
        """Test sending critical alert to all configured channels."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Critical anomaly alert
        anomaly_data = {
            "is_anomaly": True,
            "severity": "critical",
            "anomaly_type": "negative_roi",
            "roi_percent": -60.0,
            "persona_id": "ai_jesus",
            "current_cost": 150.0,
            "revenue": 60.0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Send alert through all channels
        alert_results = await alert_manager.send_alert(anomaly_data)

        # Verify alert was sent to all critical channels
        assert "slack" in alert_results
        assert "pagerduty" in alert_results
        assert "email" in alert_results
        assert all(result["success"] for result in alert_results.values())

    @pytest.mark.asyncio
    async def test_alert_manager_send_medium_alert_slack_only(self):
        """Test sending medium severity alert only to Slack."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Medium anomaly alert
        anomaly_data = {
            "is_anomaly": True,
            "severity": "medium",
            "anomaly_type": "efficiency_drop",
            "efficiency_drop_percent": 35.0,
            "persona_id": "ai_jesus",
            "timestamp": datetime.utcnow().isoformat(),
        }

        alert_results = await alert_manager.send_alert(anomaly_data)

        # Verify alert was sent only to Slack for medium severity
        assert "slack" in alert_results
        assert alert_results["slack"]["success"] is True
        # PagerDuty and email should not be triggered for medium severity
        assert "pagerduty" not in alert_results
        assert "email" not in alert_results

    @pytest.mark.asyncio
    async def test_alert_manager_slack_message_formatting(self):
        """Test Slack alert message formatting."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        anomaly_data = {
            "is_anomaly": True,
            "severity": "high",
            "anomaly_type": "cost_spike",
            "current_cost": 0.075,
            "baseline_avg": 0.020,
            "multiplier": 3.75,
            "persona_id": "ai_jesus",
            "timestamp": datetime.utcnow().isoformat(),
        }

        slack_message = alert_manager.format_slack_message(anomaly_data)

        # Verify message formatting
        assert "COST ANOMALY DETECTED" in slack_message
        assert "cost_spike" in slack_message
        assert "ai_jesus" in slack_message
        assert "3.75x" in slack_message
        assert "$0.075" in slack_message


class TestCircuitBreaker:
    """Test suite for CircuitBreaker automated cost control responses."""

    def test_circuit_breaker_initialization(self):
        """Test that CircuitBreaker can be instantiated with thresholds.

        This will fail because CircuitBreaker doesn't exist yet!
        """
        from services.finops_engine.circuit_breaker import CircuitBreaker

        config = {
            "cost_spike_threshold": 3.0,  # 3x baseline triggers circuit breaker
            "budget_threshold": 0.90,  # 90% budget triggers circuit breaker
            "roi_threshold": -0.60,  # -60% ROI triggers circuit breaker
            "actions": {
                "throttle_requests": True,  # Reduce API request rate
                "disable_expensive_models": True,  # Switch to cheaper models
                "pause_persona": False,  # Don't fully pause (too aggressive)
                "alert_human_operator": True,  # Always alert humans
            },
        }

        circuit_breaker = CircuitBreaker(config=config)

        assert circuit_breaker is not None
        assert circuit_breaker.config == config
        assert hasattr(circuit_breaker, "should_trigger")
        assert hasattr(circuit_breaker, "execute_actions")
        assert hasattr(circuit_breaker, "throttle_requests")
        assert hasattr(circuit_breaker, "switch_to_cheaper_models")

    def test_circuit_breaker_should_trigger_cost_spike(self):
        """Test circuit breaker triggering on cost spike."""
        from services.finops_engine.circuit_breaker import CircuitBreaker

        circuit_breaker = CircuitBreaker()

        # Cost spike anomaly that should trigger circuit breaker
        anomaly_data = {
            "is_anomaly": True,
            "severity": "critical",
            "anomaly_type": "cost_spike",
            "multiplier": 4.5,  # 4.5x baseline > 3x threshold
            "persona_id": "ai_jesus",
        }

        should_trigger = circuit_breaker.should_trigger(anomaly_data)

        assert should_trigger is True

    def test_circuit_breaker_should_not_trigger_minor_anomaly(self):
        """Test circuit breaker NOT triggering on minor anomaly."""
        from services.finops_engine.circuit_breaker import CircuitBreaker

        circuit_breaker = CircuitBreaker()

        # Minor efficiency drop that should NOT trigger circuit breaker
        anomaly_data = {
            "is_anomaly": True,
            "severity": "medium",
            "anomaly_type": "efficiency_drop",
            "efficiency_drop_percent": 25.0,  # Only 25% drop
            "persona_id": "ai_jesus",
        }

        should_trigger = circuit_breaker.should_trigger(anomaly_data)

        assert should_trigger is False

    @pytest.mark.asyncio
    async def test_circuit_breaker_execute_throttling_action(self):
        """Test circuit breaker executing request throttling."""
        from services.finops_engine.circuit_breaker import CircuitBreaker

        circuit_breaker = CircuitBreaker()

        # Critical anomaly requiring throttling
        anomaly_data = {
            "is_anomaly": True,
            "severity": "critical",
            "anomaly_type": "cost_spike",
            "multiplier": 5.0,
            "persona_id": "ai_jesus",
        }

        action_results = await circuit_breaker.execute_actions(anomaly_data)

        # Verify throttling action was executed
        assert "throttle_requests" in action_results
        assert action_results["throttle_requests"]["executed"] is True
        assert "new_rate_limit" in action_results["throttle_requests"]


class TestAnomalyDetectionPipeline:
    """Integration tests for the complete anomaly detection pipeline."""

    @pytest.mark.asyncio
    async def test_anomaly_detection_pipeline_under_60_seconds(self):
        """Test complete anomaly detection pipeline meets <60 second response time.

        This will fail until we integrate all components!
        """
        from services.finops_engine.cost_anomaly_detector import CostAnomalyDetector
        from services.finops_engine.alert_manager import AlertManager
        from services.finops_engine.circuit_breaker import CircuitBreaker
        import time

        # Initialize components
        detector = CostAnomalyDetector()
        alert_manager = AlertManager()
        circuit_breaker = CircuitBreaker()

        # Start timing the pipeline
        start_time = time.time()

        # 1. Detect anomaly
        baseline_costs = [0.015, 0.018, 0.020, 0.017, 0.019]
        current_cost = 0.070  # 3.9x baseline = anomaly

        anomaly_result = detector.detect_statistical_anomaly(
            current_cost=current_cost,
            baseline_costs=baseline_costs,
            persona_id="ai_jesus",
        )

        # 2. Send alerts if anomaly detected
        if anomaly_result["is_anomaly"]:
            await alert_manager.send_alert(anomaly_result)

        # 3. Execute circuit breaker actions if needed
        if circuit_breaker.should_trigger(anomaly_result):
            await circuit_breaker.execute_actions(anomaly_result)

        end_time = time.time()
        pipeline_duration = end_time - start_time

        # Verify pipeline completed under 60 seconds
        assert pipeline_duration < 60.0, (
            f"Pipeline took {pipeline_duration:.2f}s, exceeds 60s requirement"
        )

        # Verify anomaly was detected and handled
        assert anomaly_result["is_anomaly"] is True
        assert anomaly_result["severity"] == "high"

    @pytest.mark.asyncio
    async def test_integration_with_viral_finops_engine(self):
        """Test integration with existing ViralFinOpsEngine."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        # Initialize engine with anomaly detection enabled
        config = {
            "anomaly_detection_enabled": True,
            "anomaly_check_interval_seconds": 30,  # Check every 30 seconds
            "cost_threshold_per_post": 0.02,
        }

        engine = ViralFinOpsEngine(config=config)

        # Verify anomaly detection components are integrated
        assert hasattr(engine, "anomaly_detector")
        assert hasattr(engine, "alert_manager")
        assert hasattr(engine, "circuit_breaker")
        assert hasattr(engine, "check_for_anomalies")

        # Test anomaly checking method exists
        anomaly_check_result = await engine.check_for_anomalies(persona_id="ai_jesus")

        # Should return anomaly status
        assert "anomalies_detected" in anomaly_check_result
        assert "alerts_sent" in anomaly_check_result
        assert "actions_taken" in anomaly_check_result
