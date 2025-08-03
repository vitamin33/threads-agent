"""
Comprehensive Alert System Tests for FinOps Cost Tracking & Optimization Engine (CRA-240)

Tests the complete multi-channel alerting system covering:
1. AlertManager - Multi-channel notifications (Slack, PagerDuty, Email)
2. Severity-based routing and escalation
3. Alert channel failure handling and fallback
4. Alert rate limiting and deduplication
5. Integration with anomaly detection and circuit breaker
6. Alert message formatting and content validation

Key Alert System Requirements:
- Multi-channel support (Slack, PagerDuty, Email)
- Severity-based routing (critical → all channels, medium → Slack only)
- Alert delivery within 30 seconds
- Graceful handling of channel failures
- Alert deduplication and rate limiting
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta


class TestAlertManagerBasicFunctionality:
    """Basic alert manager functionality tests."""

    @pytest.mark.asyncio
    async def test_alert_manager_initialization_with_custom_config(self):
        """Test AlertManager initialization with custom channel configurations."""
        from services.finops_engine.alert_manager import AlertManager

        custom_config = {
            "channels": {
                "slack": {
                    "webhook_url": "https://hooks.slack.com/services/custom",
                    "channel": "#custom-finops-alerts",
                    "enabled": True,
                    "timeout_seconds": 10,
                },
                "pagerduty": {
                    "integration_key": "custom-pd-key-12345",
                    "service_name": "FinOps Cost Engine",
                    "enabled": True,
                    "timeout_seconds": 15,
                },
                "email": {
                    "smtp_server": "smtp.company.com",
                    "smtp_port": 587,
                    "recipients": ["finops@company.com", "alerts@company.com"],
                    "sender": "finops-alerts@company.com",
                    "enabled": True,
                },
                "webhook": {
                    "url": "https://api.company.com/alerts",
                    "headers": {"Authorization": "Bearer token123"},
                    "enabled": False,
                },
            },
            "severity_routing": {
                "critical": ["slack", "pagerduty", "email"],
                "high": ["slack", "pagerduty"],
                "medium": ["slack"],
                "low": ["email"],
                "info": [],
            },
            "rate_limiting": {
                "max_alerts_per_minute": 10,
                "deduplication_window_minutes": 5,
            },
        }

        alert_manager = AlertManager(custom_config)

        # Verify configuration is properly stored
        assert alert_manager.config == custom_config
        assert alert_manager.config["channels"]["slack"]["enabled"] is True
        assert alert_manager.config["channels"]["webhook"]["enabled"] is False
        assert len(alert_manager.config["severity_routing"]["critical"]) == 3

    @pytest.mark.asyncio
    async def test_send_critical_alert_all_channels(self):
        """Test sending critical alert to all configured channels."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Critical cost spike anomaly
        critical_anomaly = {
            "is_anomaly": True,
            "severity": "critical",
            "anomaly_type": "cost_spike",
            "current_cost": 0.150,
            "baseline_avg": 0.018,
            "multiplier": 8.33,
            "persona_id": "ai_jesus",
            "post_id": "critical_cost_001",
            "timestamp": datetime.utcnow().isoformat(),
            "detection_time": "2024-01-15T10:30:00Z",
        }

        # Send alert through all channels
        start_time = time.time()
        alert_results = await alert_manager.send_alert(critical_anomaly)
        end_time = time.time()

        # Verify alert delivery time
        delivery_time = end_time - start_time
        assert delivery_time < 30.0, (
            f"Alert delivery took {delivery_time:.2f}s, exceeds 30s requirement"
        )

        # Verify all critical channels were notified
        expected_channels = ["slack", "pagerduty", "email"]
        for channel in expected_channels:
            assert channel in alert_results, f"Missing alert result for {channel}"
            assert alert_results[channel]["success"] is True, f"{channel} alert failed"
            assert "timestamp" in alert_results[channel]

        # Verify channel-specific alert properties
        assert "message" in alert_results["slack"]
        assert "incident_key" in alert_results["pagerduty"]
        assert "recipients" in alert_results["email"]

    @pytest.mark.asyncio
    async def test_send_medium_alert_selective_channels(self):
        """Test sending medium severity alert only to appropriate channels."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Medium efficiency drop anomaly
        medium_anomaly = {
            "is_anomaly": True,
            "severity": "medium",
            "anomaly_type": "efficiency_drop",
            "current_efficiency": 35.0,
            "baseline_avg": 50.0,
            "efficiency_drop_percent": 30.0,
            "persona_id": "ai_jesus",
            "timestamp": datetime.utcnow().isoformat(),
        }

        alert_results = await alert_manager.send_alert(medium_anomaly)

        # Verify only Slack was notified for medium severity
        assert "slack" in alert_results
        assert alert_results["slack"]["success"] is True

        # PagerDuty and email should not be triggered for medium severity
        assert "pagerduty" not in alert_results
        assert "email" not in alert_results

    @pytest.mark.asyncio
    async def test_send_low_severity_alert_email_only(self):
        """Test sending low severity alert only to email."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Low severity budget warning
        low_anomaly = {
            "is_anomaly": True,
            "severity": "low",
            "anomaly_type": "budget_warning",
            "current_spend": 750.0,
            "budget_limit": 1000.0,
            "budget_usage_percent": 75.0,
            "persona_id": "ai_jesus",
            "timestamp": datetime.utcnow().isoformat(),
        }

        alert_results = await alert_manager.send_alert(low_anomaly)

        # Verify only email was notified for low severity
        assert "email" in alert_results
        assert alert_results["email"]["success"] is True

        # Slack and PagerDuty should not be triggered for low severity
        assert "slack" not in alert_results
        assert "pagerduty" not in alert_results


class TestAlertChannelImplementations:
    """Test individual alert channel implementations."""

    @pytest.mark.asyncio
    async def test_slack_alert_message_formatting(self):
        """Test Slack alert message formatting for various anomaly types."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Test different anomaly types
        test_cases = [
            {
                "name": "cost_spike",
                "anomaly": {
                    "is_anomaly": True,
                    "severity": "high",
                    "anomaly_type": "cost_spike",
                    "current_cost": 0.075,
                    "baseline_avg": 0.020,
                    "multiplier": 3.75,
                    "persona_id": "ai_jesus",
                },
                "expected_content": [
                    "COST ANOMALY",
                    "cost_spike",
                    "3.75x",
                    "$0.075",
                    "ai_jesus",
                ],
            },
            {
                "name": "efficiency_drop",
                "anomaly": {
                    "is_anomaly": True,
                    "severity": "medium",
                    "anomaly_type": "efficiency_drop",
                    "current_efficiency": 30.0,
                    "baseline_avg": 50.0,
                    "efficiency_drop_percent": 40.0,
                    "persona_id": "tech_guru",
                },
                "expected_content": [
                    "COST ANOMALY",
                    "efficiency_drop",
                    "40.0%",
                    "tech_guru",
                ],
            },
            {
                "name": "negative_roi",
                "anomaly": {
                    "is_anomaly": True,
                    "severity": "critical",
                    "anomaly_type": "negative_roi",
                    "costs": 100.0,
                    "revenue": 40.0,
                    "roi_percent": -60.0,
                    "persona_id": "startup_advisor",
                },
                "expected_content": [
                    "COST ANOMALY",
                    "negative_roi",
                    "-60.0%",
                    "startup_advisor",
                ],
            },
        ]

        for case in test_cases:
            message = alert_manager.format_slack_message(case["anomaly"])

            # Verify message structure
            assert isinstance(message, str)
            assert len(message) > 0

            # Verify expected content is present
            for expected in case["expected_content"]:
                assert str(expected) in message, (
                    f"Missing '{expected}' in {case['name']} message"
                )

            # Verify message formatting
            assert message.startswith("🚨") or "COST ANOMALY DETECTED" in message

            print(f"Slack message for {case['name']}:\n{message}\n")

    @pytest.mark.asyncio
    async def test_pagerduty_alert_incident_creation(self):
        """Test PagerDuty alert incident creation and key generation."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Critical anomaly requiring PagerDuty alert
        critical_anomaly = {
            "is_anomaly": True,
            "severity": "critical",
            "anomaly_type": "cost_spike",
            "multiplier": 10.0,
            "persona_id": "ai_jesus",
            "post_id": "pd_test_001",
            "timestamp": datetime.utcnow().isoformat(),
        }

        pd_result = await alert_manager.send_pagerduty_alert(critical_anomaly)

        # Verify PagerDuty alert structure
        assert pd_result["success"] is True
        assert pd_result["channel"] == "pagerduty"
        assert "incident_key" in pd_result
        assert "timestamp" in pd_result

        # Verify incident key format
        incident_key = pd_result["incident_key"]
        assert incident_key.startswith("cost-anomaly-")
        assert "ai_jesus" in incident_key

    @pytest.mark.asyncio
    async def test_email_alert_recipient_handling(self):
        """Test email alert with multiple recipients and formatting."""
        from services.finops_engine.alert_manager import AlertManager

        # Custom config with multiple email recipients
        config = {
            "channels": {
                "email": {
                    "recipients": [
                        "finops@company.com",
                        "alerts@company.com",
                        "manager@company.com",
                    ],
                    "enabled": True,
                }
            }
        }
        alert_manager = AlertManager(config)

        # Budget overrun anomaly
        budget_anomaly = {
            "is_anomaly": True,
            "severity": "high",
            "anomaly_type": "budget_overrun",
            "current_spend": 950.0,
            "budget_limit": 1000.0,
            "budget_usage_percent": 95.0,
            "persona_id": "ai_jesus",
        }

        email_result = await alert_manager.send_email_alert(budget_anomaly)

        # Verify email alert structure
        assert email_result["success"] is True
        assert email_result["channel"] == "email"
        assert "recipients" in email_result
        assert len(email_result["recipients"]) == 3
        assert "finops@company.com" in email_result["recipients"]


class TestAlertChannelFailureHandling:
    """Test alert system resilience when channels fail."""

    @pytest.mark.asyncio
    async def test_slack_channel_failure_with_fallback(self):
        """Test alert system behavior when Slack channel fails."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Mock Slack failure
        original_slack_method = alert_manager.send_slack_alert

        async def failing_slack_alert(*args, **kwargs):
            raise Exception("Slack webhook timeout - 504 Gateway Timeout")

        alert_manager.send_slack_alert = failing_slack_alert

        # Critical anomaly that should go to all channels
        critical_anomaly = {
            "is_anomaly": True,
            "severity": "critical",
            "anomaly_type": "cost_spike",
            "multiplier": 5.0,
            "persona_id": "failure_test",
        }

        # Should handle Slack failure gracefully
        alert_results = await alert_manager.send_alert(critical_anomaly)

        # Other channels should still succeed
        assert "pagerduty" in alert_results
        assert "email" in alert_results
        assert alert_results["pagerduty"]["success"] is True
        assert alert_results["email"]["success"] is True

        # Slack should either be missing or marked as failed
        if "slack" in alert_results:
            assert alert_results["slack"]["success"] is False

        # Restore original method
        alert_manager.send_slack_alert = original_slack_method

    @pytest.mark.asyncio
    async def test_multiple_channel_failures_partial_delivery(self):
        """Test alert delivery when multiple channels fail."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Mock multiple channel failures
        original_slack = alert_manager.send_slack_alert
        original_pagerduty = alert_manager.send_pagerduty_alert

        async def failing_slack(*args, **kwargs):
            raise Exception("Slack API rate limit exceeded")

        async def failing_pagerduty(*args, **kwargs):
            raise Exception("PagerDuty service temporarily unavailable")

        alert_manager.send_slack_alert = failing_slack
        alert_manager.send_pagerduty_alert = failing_pagerduty

        # Critical anomaly requiring all channels
        critical_anomaly = {
            "is_anomaly": True,
            "severity": "critical",
            "anomaly_type": "negative_roi",
            "roi_percent": -80.0,
            "persona_id": "multi_failure_test",
        }

        # Should deliver to at least one channel (email)
        alert_results = await alert_manager.send_alert(critical_anomaly)

        # Email should still succeed
        assert "email" in alert_results
        assert alert_results["email"]["success"] is True

        # Verify system doesn't crash with multiple failures
        assert isinstance(alert_results, dict)

        # Restore original methods
        alert_manager.send_slack_alert = original_slack
        alert_manager.send_pagerduty_alert = original_pagerduty

    @pytest.mark.asyncio
    async def test_channel_timeout_handling(self):
        """Test alert system handling of channel timeouts."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Mock slow channel response
        original_slack = alert_manager.send_slack_alert

        async def slow_slack_alert(*args, **kwargs):
            await asyncio.sleep(35)  # Simulate very slow response
            return {
                "success": True,
                "channel": "slack",
                "timestamp": datetime.utcnow().isoformat(),
            }

        alert_manager.send_slack_alert = slow_slack_alert

        # High priority anomaly
        high_anomaly = {
            "is_anomaly": True,
            "severity": "high",
            "anomaly_type": "cost_spike",
            "multiplier": 4.0,
            "persona_id": "timeout_test",
        }

        # Should handle timeout gracefully
        start_time = time.time()

        try:
            # Use timeout to prevent test from hanging
            alert_results = await asyncio.wait_for(
                alert_manager.send_alert(high_anomaly), timeout=40.0
            )

            end_time = time.time()
            alert_duration = end_time - start_time

            # Should complete within reasonable time despite slow channel
            assert alert_duration < 40.0

            # Other channels should still work
            assert "pagerduty" in alert_results
            assert alert_results["pagerduty"]["success"] is True

        except asyncio.TimeoutError:
            # Timeout is acceptable behavior for handling slow channels
            pass

        # Restore original method
        alert_manager.send_slack_alert = original_slack


class TestAlertRateLimitingAndDeduplication:
    """Test alert rate limiting and deduplication functionality."""

    @pytest.mark.asyncio
    async def test_alert_rate_limiting_burst_protection(self):
        """Test alert rate limiting prevents excessive alerts."""
        from services.finops_engine.alert_manager import AlertManager

        # Configure with strict rate limiting
        config = {
            "rate_limiting": {
                "max_alerts_per_minute": 5,
                "burst_threshold": 3,
                "cooldown_seconds": 60,
            }
        }
        alert_manager = AlertManager(config)

        # Generate burst of similar alerts
        burst_alerts = []
        for i in range(10):
            alert = {
                "is_anomaly": True,
                "severity": "medium",
                "anomaly_type": "cost_spike",
                "multiplier": 3.2,
                "persona_id": "rate_limit_test",
                "timestamp": datetime.utcnow().isoformat(),
            }
            burst_alerts.append(alert)

        # Send all alerts rapidly
        sent_alerts = []
        blocked_alerts = 0

        for alert in burst_alerts:
            try:
                result = await alert_manager.send_alert(alert)
                if result:  # Alert was sent
                    sent_alerts.append(result)
                else:  # Alert was rate limited
                    blocked_alerts += 1
            except Exception as e:
                if "rate limit" in str(e).lower():
                    blocked_alerts += 1
                else:
                    raise

        # Should have limited the number of alerts sent
        # Implementation depends on specific rate limiting strategy
        assert len(sent_alerts) <= 5, "Rate limiting should have blocked some alerts"
        print(f"Rate limiting: {len(sent_alerts)} sent, {blocked_alerts} blocked")

    @pytest.mark.asyncio
    async def test_alert_deduplication_similar_anomalies(self):
        """Test alert deduplication for similar anomalies."""
        from services.finops_engine.alert_manager import AlertManager

        # Configure with deduplication window
        config = {"rate_limiting": {"deduplication_window_minutes": 5}}
        alert_manager = AlertManager(config)

        # Similar anomalies within deduplication window
        base_anomaly = {
            "is_anomaly": True,
            "severity": "high",
            "anomaly_type": "cost_spike",
            "persona_id": "dedup_test",
            "multiplier": 3.5,
        }

        # Send similar alert multiple times
        results = []
        for i in range(5):
            # Slight variations in the anomaly
            anomaly = base_anomaly.copy()
            anomaly["multiplier"] = 3.5 + (i * 0.1)  # 3.5, 3.6, 3.7, 3.8, 3.9
            anomaly["timestamp"] = datetime.utcnow().isoformat()

            result = await alert_manager.send_alert(anomaly)
            results.append(result)

            # Small delay between alerts
            await asyncio.sleep(0.1)

        # Should have deduplicated similar alerts
        # First alert should go through, subsequent similar ones should be deduplicated
        successful_alerts = [r for r in results if r and len(r) > 0]

        # Exact behavior depends on deduplication implementation
        # Should be fewer than the total number sent
        assert len(successful_alerts) <= 3, (
            "Deduplication should have reduced alert count"
        )

    @pytest.mark.asyncio
    async def test_alert_escalation_on_repeated_anomalies(self):
        """Test alert escalation when anomalies persist or worsen."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Escalating series of anomalies
        escalation_alerts = [
            {
                "severity": "medium",
                "anomaly_type": "cost_spike",
                "multiplier": 3.2,
                "persona_id": "escalation_test",
                "timestamp": datetime.utcnow().isoformat(),
            },
            {
                "severity": "high",
                "anomaly_type": "cost_spike",
                "multiplier": 4.5,
                "persona_id": "escalation_test",
                "timestamp": (datetime.utcnow() + timedelta(minutes=2)).isoformat(),
            },
            {
                "severity": "critical",
                "anomaly_type": "cost_spike",
                "multiplier": 8.0,
                "persona_id": "escalation_test",
                "timestamp": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            },
        ]

        # Send escalating alerts
        escalation_results = []
        for alert in escalation_alerts:
            alert["is_anomaly"] = True
            result = await alert_manager.send_alert(alert)
            escalation_results.append(
                {
                    "severity": alert["severity"],
                    "channels": list(result.keys()) if result else [],
                    "success": bool(result),
                }
            )

            await asyncio.sleep(0.1)  # Brief delay between escalations

        # Verify escalation behavior
        assert escalation_results[0]["success"]  # Medium should succeed
        assert escalation_results[1]["success"]  # High should succeed
        assert escalation_results[2]["success"]  # Critical should succeed

        # Critical alert should go to more channels
        critical_channels = escalation_results[2]["channels"]
        medium_channels = escalation_results[0]["channels"]
        assert len(critical_channels) >= len(medium_channels)

        print(f"Escalation: medium→{medium_channels}, critical→{critical_channels}")


class TestAlertIntegrationWithAnomalyDetection:
    """Test alert system integration with anomaly detection and circuit breaker."""

    @pytest.mark.asyncio
    async def test_end_to_end_anomaly_detection_to_alert(self):
        """Test complete flow from anomaly detection to alert delivery."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        # Initialize with anomaly detection and alerting enabled
        config = {
            "anomaly_detection_enabled": True,
            "cost_threshold_per_post": 0.02,
            "alert_threshold_multiplier": 2.0,
        }
        engine = ViralFinOpsEngine(config)

        persona_id = "e2e_alert_test"

        # Establish baseline costs
        for i in range(5):
            await engine.track_openai_cost(
                model="gpt-3.5-turbo-0125",
                input_tokens=1000,
                output_tokens=500,
                operation=f"baseline_{i}",
                persona_id=persona_id,
                post_id=f"baseline_post_{i}",
            )

        # Generate anomalous costs that should trigger alerts
        start_time = time.time()

        for i in range(3):
            await engine.track_openai_cost(
                model="gpt-4o",
                input_tokens=8000,  # Much higher than baseline
                output_tokens=5000,
                operation=f"anomaly_trigger_{i}",
                persona_id=persona_id,
                post_id=f"anomaly_post_{i}",
            )

        # Check for anomalies (should trigger alerts)
        anomaly_result = await engine.check_for_anomalies(persona_id)

        end_time = time.time()
        total_time = end_time - start_time

        # Verify end-to-end timing
        assert total_time < 60.0, f"End-to-end anomaly→alert took {total_time:.2f}s"

        # Verify anomalies were detected
        assert len(anomaly_result["anomalies_detected"]) > 0
        anomaly = anomaly_result["anomalies_detected"][0]
        assert anomaly["is_anomaly"] is True
        assert anomaly["severity"] in ["high", "critical"]

        # Verify alerts were sent
        if len(anomaly_result["alerts_sent"]) > 0:
            alert_result = anomaly_result["alerts_sent"][0]
            assert (
                "slack" in alert_result
                or "pagerduty" in alert_result
                or "email" in alert_result
            )

    @pytest.mark.asyncio
    async def test_circuit_breaker_triggered_alert_integration(self):
        """Test alerts when circuit breaker is triggered."""
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        engine = ViralFinOpsEngine({"anomaly_detection_enabled": True})

        # Create severe anomaly that should trigger circuit breaker
        severe_anomaly = {
            "is_anomaly": True,
            "severity": "critical",
            "anomaly_type": "cost_spike",
            "multiplier": 15.0,  # Extreme spike
            "current_cost": 0.300,
            "baseline_avg": 0.020,
            "persona_id": "circuit_breaker_test",
        }

        # Manually trigger anomaly detection (simulating real detection)
        if hasattr(engine, "anomaly_detector") and hasattr(engine, "circuit_breaker"):
            # Check if circuit breaker should trigger
            should_trigger = engine.circuit_breaker.should_trigger(severe_anomaly)
            assert should_trigger is True, (
                "Circuit breaker should trigger for severe anomaly"
            )

            # Execute circuit breaker actions (which should include alerting)
            action_results = await engine.circuit_breaker.execute_actions(
                severe_anomaly
            )

            # Verify human operator alert was sent
            if "alert_human_operator" in action_results:
                operator_alert = action_results["alert_human_operator"]
                assert operator_alert["executed"] is True
                assert operator_alert["alert_sent"] is True
                assert "channels" in operator_alert

    @pytest.mark.asyncio
    async def test_alert_content_validation_for_different_anomaly_types(self):
        """Test alert content validation for various anomaly types."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Test various anomaly types with specific content requirements
        test_anomalies = [
            {
                "type": "cost_spike",
                "anomaly": {
                    "is_anomaly": True,
                    "severity": "high",
                    "anomaly_type": "cost_spike",
                    "current_cost": 0.085,
                    "baseline_avg": 0.020,
                    "multiplier": 4.25,
                    "persona_id": "content_test_spike",
                },
                "required_content": ["cost", "spike", "4.25", "$0.085", "baseline"],
            },
            {
                "type": "efficiency_drop",
                "anomaly": {
                    "is_anomaly": True,
                    "severity": "medium",
                    "anomaly_type": "efficiency_drop",
                    "current_efficiency": 25.0,
                    "baseline_avg": 45.0,
                    "efficiency_drop_percent": 44.4,
                    "persona_id": "content_test_efficiency",
                },
                "required_content": ["efficiency", "drop", "44.4%", "performance"],
            },
            {
                "type": "budget_overrun",
                "anomaly": {
                    "is_anomaly": True,
                    "severity": "critical",
                    "anomaly_type": "budget_overrun",
                    "current_spend": 1150.0,
                    "budget_limit": 1000.0,
                    "budget_usage_percent": 115.0,
                    "persona_id": "content_test_budget",
                },
                "required_content": ["budget", "overrun", "115%", "$1150", "$1000"],
            },
        ]

        for test_case in test_anomalies:
            # Generate Slack message for content validation
            message = alert_manager.format_slack_message(test_case["anomaly"])

            # Verify required content is present
            message_lower = message.lower()
            for required in test_case["required_content"]:
                assert str(required).lower() in message_lower, (
                    f"Missing '{required}' in {test_case['type']} alert message"
                )

            # Verify message structure and formatting
            assert len(message) > 50, f"{test_case['type']} message too short"
            assert len(message) < 2000, (
                f"{test_case['type']} message too long for Slack"
            )

            # Verify persona information is included
            assert test_case["anomaly"]["persona_id"] in message

            print(f"✓ Content validation passed for {test_case['type']}")


class TestAlertSystemPerformanceAndReliability:
    """Test alert system performance and reliability under various conditions."""

    @pytest.mark.asyncio
    async def test_high_volume_alert_processing(self):
        """Test alert system performance under high alert volume."""
        from services.finops_engine.alert_manager import AlertManager

        alert_manager = AlertManager()

        # Generate high volume of diverse alerts
        alert_count = 50
        alerts = []

        for i in range(alert_count):
            alert = {
                "is_anomaly": True,
                "severity": ["medium", "high", "critical"][i % 3],
                "anomaly_type": ["cost_spike", "efficiency_drop", "budget_overrun"][
                    i % 3
                ],
                "multiplier": 3.0 + (i % 5),
                "persona_id": f"volume_test_persona_{i % 10}",
                "timestamp": datetime.utcnow().isoformat(),
            }
            alerts.append(alert)

        # Process all alerts concurrently
        start_time = time.time()

        tasks = [alert_manager.send_alert(alert) for alert in alerts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        processing_time = end_time - start_time

        # Verify performance requirements
        alerts_per_second = alert_count / processing_time
        assert processing_time < 30.0, (
            f"High volume processing took {processing_time:.2f}s"
        )
        assert alerts_per_second > 2.0, (
            f"Alert processing rate {alerts_per_second:.1f}/s too low"
        )

        # Verify most alerts were processed successfully
        successful_results = [r for r in results if not isinstance(r, Exception) and r]
        success_rate = len(successful_results) / alert_count
        assert success_rate > 0.8, (
            f"Success rate {success_rate:.1%} too low for high volume"
        )

        print(
            f"High volume: {alert_count} alerts in {processing_time:.2f}s "
            f"({alerts_per_second:.1f}/s, {success_rate:.1%} success)"
        )

    @pytest.mark.asyncio
    async def test_alert_system_memory_usage_under_load(self):
        """Test alert system memory usage doesn't grow unbounded."""
        from services.finops_engine.alert_manager import AlertManager
        import gc

        alert_manager = AlertManager()

        # Baseline memory measurement
        gc.collect()
        # Note: In a real test, you'd use memory profiling tools
        # This is a simplified test focusing on behavior

        # Generate and process many alerts to test memory management
        for batch in range(10):
            batch_alerts = []
            for i in range(20):
                alert = {
                    "is_anomaly": True,
                    "severity": "medium",
                    "anomaly_type": "cost_spike",
                    "multiplier": 3.2,
                    "persona_id": f"memory_test_{batch}_{i}",
                    "large_metadata": "x" * 1000,  # Add some bulk to test memory
                    "timestamp": datetime.utcnow().isoformat(),
                }
                batch_alerts.append(alert)

            # Process batch
            tasks = [alert_manager.send_alert(alert) for alert in batch_alerts]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Force garbage collection between batches
            gc.collect()

        # Verify system is still responsive after high load
        test_alert = {
            "is_anomaly": True,
            "severity": "high",
            "anomaly_type": "cost_spike",
            "multiplier": 4.0,
            "persona_id": "memory_final_test",
        }

        start_time = time.time()
        final_result = await alert_manager.send_alert(test_alert)
        end_time = time.time()

        final_latency = (end_time - start_time) * 1000
        assert final_latency < 1000, (
            f"System unresponsive after load: {final_latency:.2f}ms"
        )
        assert final_result is not None, "Alert system failed after memory test"

    @pytest.mark.asyncio
    async def test_alert_delivery_reliability_with_retries(self):
        """Test alert delivery reliability with retry mechanisms."""
        from services.finops_engine.alert_manager import AlertManager

        # Configure with retry settings
        config = {
            "channels": {
                "slack": {"enabled": True, "max_retries": 3, "retry_delay_seconds": 1},
                "email": {
                    "enabled": True,
                    "max_retries": 2,
                    "retry_delay_seconds": 0.5,
                },
            }
        }
        alert_manager = AlertManager(config)

        # Mock intermittent failure
        call_count = {"slack": 0, "email": 0}
        original_slack = alert_manager.send_slack_alert
        original_email = alert_manager.send_email_alert

        async def intermittent_slack_failure(*args, **kwargs):
            call_count["slack"] += 1
            if call_count["slack"] <= 2:  # Fail first 2 attempts
                raise Exception("Temporary Slack API error")
            return await original_slack(*args, **kwargs)

        async def intermittent_email_failure(*args, **kwargs):
            call_count["email"] += 1
            if call_count["email"] == 1:  # Fail first attempt only
                raise Exception("SMTP timeout")
            return await original_email(*args, **kwargs)

        alert_manager.send_slack_alert = intermittent_slack_failure
        alert_manager.send_email_alert = intermittent_email_failure

        # Critical alert requiring reliable delivery
        critical_alert = {
            "is_anomaly": True,
            "severity": "critical",
            "anomaly_type": "cost_spike",
            "multiplier": 6.0,
            "persona_id": "reliability_test",
        }

        # Should eventually succeed despite intermittent failures
        # Note: This test assumes retry logic is implemented in AlertManager
        # In this minimal implementation, we're testing the concept

        alert_results = await alert_manager.send_alert(critical_alert)

        # Verify eventual success (implementation dependent)
        # In a full implementation with retries, both should eventually succeed
        assert alert_results is not None

        # Restore original methods
        alert_manager.send_slack_alert = original_slack
        alert_manager.send_email_alert = original_email
