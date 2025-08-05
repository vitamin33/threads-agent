"""
Intelligent Anomaly Detection system for CRA-241

Detects:
1. Cost anomalies (target: <$0.02/post, alert if >25% above)
2. Viral coefficient drops (alert if <70% of baseline)
3. Pattern fatigue (alert if fatigue score >0.8)

Features:
- Multiple severity levels: critical, warning, info
- Confidence scores (0.0-1.0) for each anomaly
- Process alerts with <60s SLA
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class AnomalyEvent:
    """Dataclass representing an anomaly event with metadata."""

    metric_name: str
    current_value: float
    baseline: float
    severity: str  # critical, warning, info
    confidence: float  # 0.0-1.0
    context: Dict


class AnomalyDetector:
    """Intelligent anomaly detection system with multiple detection algorithms."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize anomaly detector with optional configuration."""
        self.config = config or {}

    def detect_cost_anomaly(
        self, current_cost: float, baseline_cost: float, persona_id: str
    ) -> Optional[AnomalyEvent]:
        """Detect cost anomalies based on threshold and percentage rules."""
        # Cost threshold: $0.02/post, alert if >25% above
        cost_threshold = self.config.get("cost_threshold", 0.02)
        alert_percent = self.config.get("cost_alert_percent", 25)

        # Calculate percentage increase from baseline
        if baseline_cost > 0:
            percent_increase = ((current_cost - baseline_cost) / baseline_cost) * 100
        else:
            percent_increase = 0

        # Check if cost is above threshold AND above alert percentage
        if current_cost > cost_threshold or percent_increase >= alert_percent:
            # Determine severity based on how far above threshold
            if percent_increase >= 100:  # 100% above baseline
                severity = "critical"
                confidence = 0.9
            elif percent_increase >= 50:  # 50% above baseline
                severity = "warning"
                confidence = 0.8
            else:  # 25%+ above baseline
                severity = "warning"
                confidence = 0.7

            return AnomalyEvent(
                metric_name="cost_per_post",
                current_value=current_cost,
                baseline=baseline_cost,
                severity=severity,
                confidence=confidence,
                context={
                    "persona_id": persona_id,
                    "percent_increase": percent_increase,
                },
            )

        return None

    def detect_viral_coefficient_drop(
        self, current_coefficient: float, baseline_coefficient: float, persona_id: str
    ) -> Optional[AnomalyEvent]:
        """Detect viral coefficient drops below 70% of baseline."""
        # Alert if <70% of baseline
        threshold_percent = self.config.get("viral_coefficient_threshold", 70)

        if baseline_coefficient > 0:
            current_percent = (current_coefficient / baseline_coefficient) * 100
        else:
            current_percent = 100

        # Check if current coefficient is at or below threshold
        if current_percent <= threshold_percent:
            # Determine severity based on how low it dropped
            if current_percent <= 40:  # Very critical drop
                severity = "critical"
                confidence = 0.9
            elif current_percent <= 55:  # Moderate drop
                severity = "warning"
                confidence = 0.8
            else:  # At threshold (70%)
                severity = "warning"
                confidence = 0.6

            return AnomalyEvent(
                metric_name="viral_coefficient",
                current_value=current_coefficient,
                baseline=baseline_coefficient,
                severity=severity,
                confidence=confidence,
                context={"persona_id": persona_id, "current_percent": current_percent},
            )

        return None

    def detect_pattern_fatigue(
        self, fatigue_score: float, persona_id: str
    ) -> Optional[AnomalyEvent]:
        """Detect pattern fatigue when score exceeds 0.8."""
        # Alert if fatigue score >= 0.8
        threshold = self.config.get("pattern_fatigue_threshold", 0.8)

        if fatigue_score >= threshold:
            # Determine severity based on fatigue level
            if fatigue_score >= 0.95:  # Very high fatigue
                severity = "critical"
                confidence = 0.9
            elif fatigue_score >= 0.9:  # High fatigue
                severity = "warning"
                confidence = 0.8
            else:  # At threshold (0.8)
                severity = "warning"
                confidence = 0.7

            return AnomalyEvent(
                metric_name="pattern_fatigue",
                current_value=fatigue_score,
                baseline=threshold,
                severity=severity,
                confidence=confidence,
                context={"persona_id": persona_id, "fatigue_score": fatigue_score},
            )

        return None
