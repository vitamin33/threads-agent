"""Tests for early kill monitoring system."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from services.performance_monitor.early_kill import (
    EarlyKillMonitor,
    VariantPerformance,
    KillDecision,
    TimeoutStatus,
)


class TestEarlyKillMonitor:
    """Test suite for early kill monitoring functionality."""
    
    def test_monitor_starts_automatically_when_variant_posted(self):
        """Test that monitoring begins automatically when a variant is posted."""
        # Arrange
        monitor = EarlyKillMonitor()
        variant_id = "variant_123"
        persona_id = "persona_abc"
        expected_engagement_rate = 0.06  # 6% expected
        
        # Act
        monitoring_session = monitor.start_monitoring(
            variant_id=variant_id,
            persona_id=persona_id,
            expected_engagement_rate=expected_engagement_rate,
            post_timestamp=datetime.now()
        )
        
        # Assert
        assert monitoring_session is not None
        assert monitoring_session.variant_id == variant_id
        assert monitoring_session.is_active == True
        assert monitoring_session.started_at is not None
    
    def test_kill_decision_when_engagement_below_threshold(self):
        """Test that variants with <50% expected ER after 10 interactions are marked for killing."""
        # Arrange
        monitor = EarlyKillMonitor()
        variant_id = "variant_123"
        expected_engagement_rate = 0.06  # 6% expected
        
        # Start monitoring
        monitor.start_monitoring(
            variant_id=variant_id,
            persona_id="persona_abc",
            expected_engagement_rate=expected_engagement_rate,
            post_timestamp=datetime.now()
        )
        
        # Create performance data with low engagement (2% actual vs 6% expected = 33%)
        performance_data = VariantPerformance(
            variant_id=variant_id,
            total_views=500,
            total_interactions=10,  # Exactly 10 interactions
            engagement_rate=0.02,  # 2% actual (less than 50% of 6% expected)
            last_updated=datetime.now()
        )
        
        # Act
        decision = monitor.evaluate_performance(variant_id, performance_data)
        
        # Assert
        assert decision is not None
        assert decision.should_kill == True
        assert decision.reason == "Below 50% of expected engagement rate"
        assert decision.evaluation_time <= 5.0  # Must be under 5 seconds
    
    def test_monitoring_timeout_after_10_minutes(self):
        """Test that monitoring automatically times out after 10 minutes."""
        # Arrange
        monitor = EarlyKillMonitor()
        variant_id = "variant_123"
        post_time = datetime.now() - timedelta(minutes=11)  # 11 minutes ago
        
        # Start monitoring with old timestamp
        monitor.start_monitoring(
            variant_id=variant_id,
            persona_id="persona_abc",
            expected_engagement_rate=0.06,
            post_timestamp=post_time
        )
        
        # Act
        session_status = monitor.check_timeout(variant_id)
        
        # Assert
        assert session_status is not None
        assert session_status.timed_out == True
        assert session_status.reason == "10-minute monitoring window expired"
    
    def test_no_kill_decision_with_insufficient_interactions(self):
        """Test that no kill decision is made with less than 10 interactions."""
        # Arrange
        monitor = EarlyKillMonitor()
        variant_id = "variant_123"
        
        monitor.start_monitoring(
            variant_id=variant_id,
            persona_id="persona_abc",
            expected_engagement_rate=0.06,
            post_timestamp=datetime.now()
        )
        
        # Performance data with only 9 interactions
        performance_data = VariantPerformance(
            variant_id=variant_id,
            total_views=450,
            total_interactions=9,  # Less than 10
            engagement_rate=0.02,  # Low engagement
            last_updated=datetime.now()
        )
        
        # Act
        decision = monitor.evaluate_performance(variant_id, performance_data)
        
        # Assert
        assert decision is None  # No decision made yet
    
    def test_no_kill_decision_when_performance_above_threshold(self):
        """Test that variants above 50% threshold are not killed."""
        # Arrange
        monitor = EarlyKillMonitor()
        variant_id = "variant_123"
        expected_rate = 0.06
        
        monitor.start_monitoring(
            variant_id=variant_id,
            persona_id="persona_abc",
            expected_engagement_rate=expected_rate,
            post_timestamp=datetime.now()
        )
        
        # Performance at 60% of expected (3.6% actual vs 6% expected)
        performance_data = VariantPerformance(
            variant_id=variant_id,
            total_views=500,
            total_interactions=18,
            engagement_rate=0.036,
            last_updated=datetime.now()
        )
        
        # Act
        decision = monitor.evaluate_performance(variant_id, performance_data)
        
        # Assert
        assert decision is None  # Should not kill