"""
AI system alerts and monitoring for drift detection and anomalies.

Provides automated alerting for model drift, performance degradation,
cost overruns, and security incidents.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Literal
from collections import deque
import logging

logger = logging.getLogger(__name__)

AlertSeverity = Literal["INFO", "WARNING", "ERROR", "CRITICAL"]
AlertType = Literal[
    "MODEL_DRIFT", "HIGH_LATENCY", "HIGH_COST", "HIGH_ERROR_RATE",
    "SECURITY_INCIDENT", "RESOURCE_EXHAUSTION", "QUALITY_DEGRADATION"
]


class Alert:
    """Represents a system alert."""
    
    def __init__(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        action_required: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = f"{alert_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.type = alert_type
        self.severity = severity
        self.message = message
        self.action_required = action_required
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.acknowledged = False
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for API responses."""
        return {
            'id': self.id,
            'type': self.type,
            'severity': self.severity,
            'message': self.message,
            'action_required': self.action_required,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged,
            'metadata': self.metadata
        }


class AIAlertManager:
    """Manage AI system alerts and thresholds."""
    
    def __init__(self, max_alerts: int = 1000):
        """
        Initialize alert manager.
        
        Args:
            max_alerts: Maximum number of alerts to keep in memory
        """
        self.alerts: deque[Alert] = deque(maxlen=max_alerts)
        self.active_alerts: Dict[str, Alert] = {}  # Currently active alerts by type
        
        # Configurable thresholds
        self.thresholds = {
            'latency_p95_ms': 2000,
            'latency_p99_ms': 5000,
            'error_rate': 0.05,  # 5%
            'cost_per_request': 0.015,  # $0.015
            'drift_threshold': 10,  # 10% confidence drift
            'min_confidence': 0.7,
            'security_incident_threshold': 5  # incidents per hour
        }
        
        # Alert suppression to prevent spam
        self.last_alert_time: Dict[AlertType, datetime] = {}
        self.alert_cooldown = timedelta(minutes=15)  # Don't repeat same alert type for 15 min
        
    def check_and_alert(self, metrics: Dict[str, Any]) -> List[Alert]:
        """
        Check metrics and generate alerts based on thresholds.
        
        Args:
            metrics: Current system metrics
            
        Returns:
            List of new alerts triggered
        """
        alerts_triggered = []
        
        # AI System Metrics Checks
        ai_metrics = metrics.get('ai_system', {})
        
        # 1. Check for model drift
        self._check_model_drift(ai_metrics, alerts_triggered)
        
        # 2. Check for high latency
        self._check_latency(ai_metrics.get('performance', {}), alerts_triggered)
        
        # 3. Check for high costs
        self._check_costs(ai_metrics.get('cost', {}), alerts_triggered)
        
        # 4. Check for high error rates
        self._check_error_rate(ai_metrics.get('performance', {}), alerts_triggered)
        
        # 5. Check for security incidents
        self._check_security(metrics.get('ai_safety', {}), alerts_triggered)
        
        # 6. Check for quality degradation
        self._check_quality(ai_metrics, alerts_triggered)
        
        # Store alerts
        for alert in alerts_triggered:
            self.alerts.append(alert)
            self.active_alerts[alert.type] = alert
            logger.warning(f"AI Alert triggered: {alert.type} - {alert.message}")
            
        return alerts_triggered
    
    def _check_model_drift(self, ai_metrics: Dict[str, Any], alerts: List[Alert]) -> None:
        """Check for model confidence drift."""
        confidence_trend = ai_metrics.get('drift_detection', {}).get('model_confidence_trend', '')
        
        if 'significant_drift' in confidence_trend and self._should_alert('MODEL_DRIFT'):
            drift_amount = confidence_trend.split('_')[-1]
            alert = Alert(
                alert_type='MODEL_DRIFT',
                severity='ERROR',
                message=f"Significant model confidence drift detected: {drift_amount}",
                action_required='Investigate model performance and consider retraining',
                metadata={
                    'drift_amount': drift_amount,
                    'avg_confidence': ai_metrics.get('drift_detection', {}).get('avg_confidence', 0)
                }
            )
            alerts.append(alert)
            self.last_alert_time['MODEL_DRIFT'] = datetime.utcnow()
            
        elif 'moderate_drift' in confidence_trend and self._should_alert('MODEL_DRIFT'):
            drift_amount = confidence_trend.split('_')[-1]
            alert = Alert(
                alert_type='MODEL_DRIFT',
                severity='WARNING',
                message=f"Moderate model confidence drift detected: {drift_amount}",
                action_required='Monitor closely, prepare for potential retraining',
                metadata={'drift_amount': drift_amount}
            )
            alerts.append(alert)
            self.last_alert_time['MODEL_DRIFT'] = datetime.utcnow()
    
    def _check_latency(self, performance: Dict[str, Any], alerts: List[Alert]) -> None:
        """Check for high latency issues."""
        p95_latency = performance.get('p95_inference_time_ms', 0)
        p99_latency = performance.get('p99_inference_time_ms', 0)
        
        if p99_latency > self.thresholds['latency_p99_ms'] and self._should_alert('HIGH_LATENCY'):
            alert = Alert(
                alert_type='HIGH_LATENCY',
                severity='ERROR',
                message=f"Critical latency detected: P99 {p99_latency}ms (threshold: {self.thresholds['latency_p99_ms']}ms)",
                action_required='Check model server load, consider scaling or optimization',
                metadata={
                    'p95_latency_ms': p95_latency,
                    'p99_latency_ms': p99_latency,
                    'avg_latency_ms': performance.get('avg_inference_time_ms', 0)
                }
            )
            alerts.append(alert)
            self.last_alert_time['HIGH_LATENCY'] = datetime.utcnow()
            
        elif p95_latency > self.thresholds['latency_p95_ms'] and self._should_alert('HIGH_LATENCY'):
            alert = Alert(
                alert_type='HIGH_LATENCY',
                severity='WARNING',
                message=f"High latency detected: P95 {p95_latency}ms (threshold: {self.thresholds['latency_p95_ms']}ms)",
                action_required='Monitor system load and prepare to scale',
                metadata={'p95_latency_ms': p95_latency}
            )
            alerts.append(alert)
            self.last_alert_time['HIGH_LATENCY'] = datetime.utcnow()
    
    def _check_costs(self, cost_metrics: Dict[str, Any], alerts: List[Alert]) -> None:
        """Check for high inference costs."""
        cost_per_request = cost_metrics.get('cost_per_request', 0)
        
        if cost_per_request > self.thresholds['cost_per_request'] and self._should_alert('HIGH_COST'):
            monthly_projection = cost_metrics.get('monthly_projection', 0)
            alert = Alert(
                alert_type='HIGH_COST',
                severity='WARNING',
                message=f"High inference costs: ${cost_per_request:.4f}/request (projected ${monthly_projection:.0f}/month)",
                action_required='Review model selection, implement caching, or optimize prompts',
                metadata={
                    'cost_per_request': cost_per_request,
                    'monthly_projection': monthly_projection,
                    'threshold': self.thresholds['cost_per_request']
                }
            )
            alerts.append(alert)
            self.last_alert_time['HIGH_COST'] = datetime.utcnow()
    
    def _check_error_rate(self, performance: Dict[str, Any], alerts: List[Alert]) -> None:
        """Check for high error rates."""
        error_rate = performance.get('error_rate', 0)
        
        if error_rate > self.thresholds['error_rate'] and self._should_alert('HIGH_ERROR_RATE'):
            alert = Alert(
                alert_type='HIGH_ERROR_RATE',
                severity='ERROR' if error_rate > 0.1 else 'WARNING',
                message=f"High error rate detected: {error_rate:.1%} (threshold: {self.thresholds['error_rate']:.1%})",
                action_required='Investigate error logs and API health',
                metadata={
                    'error_rate': error_rate,
                    'total_requests': performance.get('total_requests', 0)
                }
            )
            alerts.append(alert)
            self.last_alert_time['HIGH_ERROR_RATE'] = datetime.utcnow()
    
    def _check_security(self, safety_metrics: Dict[str, Any], alerts: List[Alert]) -> None:
        """Check for security incidents."""
        prompt_injections = safety_metrics.get('prompt_injection_attempts_24h', 0)
        
        if prompt_injections > self.thresholds['security_incident_threshold'] and self._should_alert('SECURITY_INCIDENT'):
            alert = Alert(
                alert_type='SECURITY_INCIDENT',
                severity='CRITICAL',
                message=f"Multiple prompt injection attempts detected: {prompt_injections} in 24h",
                action_required='Review security logs and strengthen input validation',
                metadata={
                    'prompt_injections': prompt_injections,
                    'hallucination_flags': safety_metrics.get('hallucination_flags_24h', 0),
                    'content_violations': safety_metrics.get('content_violations_24h', 0)
                }
            )
            alerts.append(alert)
            self.last_alert_time['SECURITY_INCIDENT'] = datetime.utcnow()
    
    def _check_quality(self, ai_metrics: Dict[str, Any], alerts: List[Alert]) -> None:
        """Check for quality degradation."""
        avg_confidence = ai_metrics.get('drift_detection', {}).get('avg_confidence', 1.0)
        health_score = ai_metrics.get('health_score', 100)
        
        if avg_confidence < self.thresholds['min_confidence'] and self._should_alert('QUALITY_DEGRADATION'):
            alert = Alert(
                alert_type='QUALITY_DEGRADATION',
                severity='WARNING',
                message=f"Low model confidence detected: {avg_confidence:.2f} (threshold: {self.thresholds['min_confidence']})",
                action_required='Review generated content quality and model performance',
                metadata={
                    'avg_confidence': avg_confidence,
                    'health_score': health_score
                }
            )
            alerts.append(alert)
            self.last_alert_time['QUALITY_DEGRADATION'] = datetime.utcnow()
    
    def _should_alert(self, alert_type: AlertType) -> bool:
        """Check if we should generate an alert (respecting cooldown)."""
        last_time = self.last_alert_time.get(alert_type)
        if last_time is None:
            return True
        
        return datetime.utcnow() - last_time > self.alert_cooldown
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all currently active alerts."""
        return [alert.to_dict() for alert in self.active_alerts.values()]
    
    def get_recent_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        recent = list(self.alerts)[-limit:]
        recent.reverse()  # Most recent first
        return [alert.to_dict() for alert in recent]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                # Remove from active alerts
                if alert.type in self.active_alerts and self.active_alerts[alert.type].id == alert_id:
                    del self.active_alerts[alert.type]
                return True
        return False
    
    def update_threshold(self, threshold_name: str, value: float) -> None:
        """Update an alert threshold."""
        if threshold_name in self.thresholds:
            old_value = self.thresholds[threshold_name]
            self.thresholds[threshold_name] = value
            logger.info(f"Updated threshold {threshold_name}: {old_value} -> {value}")


# Global instance for easy access
ai_alerts = AIAlertManager()