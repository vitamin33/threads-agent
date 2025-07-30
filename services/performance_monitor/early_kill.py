"""Early kill monitoring system for underperforming variants."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class VariantPerformance:
    """Tracks performance metrics for a variant."""
    variant_id: str
    total_views: int
    total_interactions: int
    engagement_rate: float
    last_updated: datetime


@dataclass
class KillDecision:
    """Represents a decision to kill or keep a variant."""
    should_kill: bool
    reason: str
    evaluation_time: float


@dataclass
class MonitoringSession:
    """Represents an active monitoring session for a variant."""
    variant_id: str
    persona_id: str
    expected_engagement_rate: float
    started_at: datetime
    is_active: bool = True


@dataclass
class TimeoutStatus:
    """Status of a monitoring session timeout check."""
    timed_out: bool
    reason: str


class EarlyKillMonitor:
    """Monitors variant performance and makes early kill decisions."""
    
    def __init__(self):
        """Initialize the early kill monitor."""
        self.active_sessions = {}
    
    def start_monitoring(
        self,
        variant_id: str,
        persona_id: str,
        expected_engagement_rate: float,
        post_timestamp: datetime
    ) -> MonitoringSession:
        """Start monitoring a variant for early kill decisions."""
        session = MonitoringSession(
            variant_id=variant_id,
            persona_id=persona_id,
            expected_engagement_rate=expected_engagement_rate,
            started_at=post_timestamp,
            is_active=True
        )
        
        self.active_sessions[variant_id] = session
        return session
    
    def evaluate_performance(
        self,
        variant_id: str,
        performance_data: VariantPerformance
    ) -> Optional[KillDecision]:
        """Evaluate variant performance and decide if it should be killed."""
        import time
        start_time = time.time()
        
        # Get the monitoring session
        if variant_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[variant_id]
        
        # Check if we have enough interactions
        if performance_data.total_interactions < 10:
            return None
        
        # Calculate if performance is below 50% of expected
        threshold = session.expected_engagement_rate * 0.5
        
        if performance_data.engagement_rate < threshold:
            evaluation_time = time.time() - start_time
            return KillDecision(
                should_kill=True,
                reason="Below 50% of expected engagement rate",
                evaluation_time=evaluation_time
            )
        
        return None
    
    def check_timeout(self, variant_id: str) -> Optional[TimeoutStatus]:
        """Check if monitoring session has timed out."""
        if variant_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[variant_id]
        elapsed_time = datetime.now() - session.started_at
        
        if elapsed_time > timedelta(minutes=10):
            session.is_active = False
            return TimeoutStatus(
                timed_out=True,
                reason="10-minute monitoring window expired"
            )
        
        return TimeoutStatus(
            timed_out=False,
            reason="Still within monitoring window"
        )