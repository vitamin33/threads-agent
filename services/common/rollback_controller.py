"""
RollbackController - Automatic rollback on deployment degradation.

Part of CRA-297 CI/CD Pipeline implementation. Provides automatic rollback capabilities
with deployment health monitoring, automatic rollback triggers, and history tracking.

Requirements:
- Monitor deployment health
- Automatic rollback triggers (performance, errors, etc.)
- <30 second rollback time
- Integration with Model Registry
- Rollback history tracking

This implementation follows strict TDD practices and integrates with the
PerformanceRegressionDetector and Model Registry.

Author: TDD Implementation for CRA-297
"""

import time
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class RollbackError(Exception):
    """Raised when RollbackController encounters an error."""

    pass


class RollbackTrigger(Enum):
    """Enumeration of rollback trigger types."""

    PERFORMANCE_REGRESSION = "performance_regression"
    ERROR_RATE_SPIKE = "error_rate_spike"
    MANUAL = "manual"
    DEPLOYMENT_TIMEOUT = "deployment_timeout"
    HEALTH_CHECK_FAILURE = "health_check_failure"


@dataclass
class HealthCheck:
    """
    Represents the result of a deployment health check.

    Attributes:
        is_healthy: Whether the deployment is considered healthy
        triggers_rollback: Whether this health check should trigger rollback
        detected_issues: List of detected issue types
        has_sufficient_data: Whether there was sufficient data for analysis
        timestamp: When the health check was performed
        metrics_summary: Summary of health metrics
    """

    is_healthy: bool
    triggers_rollback: bool
    detected_issues: List[RollbackTrigger] = field(default_factory=list)
    has_sufficient_data: bool = True
    timestamp: datetime = field(default_factory=datetime.now)
    metrics_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RollbackResult:
    """
    Result of a rollback operation.

    Attributes:
        success: Whether the rollback was successful
        trigger: What triggered the rollback
        from_model: Model version rolled back from
        to_model: Model version rolled back to
        reason: Human-readable reason for rollback
        error_message: Error message if rollback failed
        duration: Time taken for rollback in seconds
        timestamp: When the rollback was executed
    """

    success: bool
    trigger: RollbackTrigger
    from_model: str
    to_model: str
    reason: Optional[str] = None
    error_message: Optional[str] = None
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RollbackEvent:
    """
    Historical record of a rollback event.

    Attributes:
        trigger: What triggered the rollback
        from_model: Model version rolled back from
        to_model: Model version rolled back to
        success: Whether the rollback was successful
        reason: Human-readable reason for rollback
        timestamp: When the rollback occurred
        duration: Time taken for rollback
        error_message: Error message if rollback failed
    """

    trigger: RollbackTrigger
    from_model: str
    to_model: str
    success: bool
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0
    error_message: Optional[str] = None


@dataclass
class RollbackStatus:
    """
    Current status of rollback monitoring.

    Attributes:
        is_monitoring: Whether rollback monitoring is active
        current_model: Currently deployed model version
        fallback_model: Model version to rollback to
        monitoring_start_time: When monitoring started
        last_health_check: Time of last health check
        rollback_count: Number of rollbacks performed
    """

    is_monitoring: bool
    current_model: Optional[str] = None
    fallback_model: Optional[str] = None
    monitoring_start_time: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    rollback_count: int = 0


class RollbackController:
    """
    Automatic rollback controller for deployment health monitoring.

    Provides comprehensive rollback capabilities including:
    - Real-time deployment health monitoring
    - Automatic rollback triggers based on performance regression
    - Manual rollback control with reason tracking
    - Sub-30 second rollback execution
    - Complete rollback history tracking
    - Integration with PerformanceRegressionDetector and Model Registry

    Integrates with existing CI/CD pipeline for automated deployment safety.
    """

    def __init__(
        self,
        performance_detector,
        model_registry,
        rollback_threshold_seconds: float = 30.0,
        health_check_interval_seconds: int = 60,
    ):
        """
        Initialize RollbackController.

        Args:
            performance_detector: PerformanceRegressionDetector instance
            model_registry: Model registry for rollback operations
            rollback_threshold_seconds: Maximum allowed rollback time
            health_check_interval_seconds: Interval between health checks

        Raises:
            RollbackError: If required components are None
        """
        if performance_detector is None:
            raise RollbackError("Performance detector cannot be None")
        if model_registry is None:
            raise RollbackError("Model registry cannot be None")

        self.performance_detector = performance_detector
        self.model_registry = model_registry
        self.rollback_threshold_seconds = rollback_threshold_seconds
        self.health_check_interval_seconds = health_check_interval_seconds

        # Current monitoring state
        self.is_monitoring = False
        self.current_model: Optional[str] = None
        self.fallback_model: Optional[str] = None
        self.monitoring_start_time: Optional[datetime] = None
        self.last_health_check: Optional[datetime] = None

        # Rollback history (in production, this would be persisted)
        self.rollback_history: List[RollbackEvent] = []

    def start_monitoring(
        self, current_model: str, fallback_model: str
    ) -> RollbackResult:
        """
        Start monitoring the deployment for automatic rollback triggers.

        Args:
            current_model: Currently deployed model version
            fallback_model: Model version to rollback to if issues are detected

        Returns:
            RollbackResult indicating whether monitoring started successfully
        """
        if self.is_monitoring:
            return RollbackResult(
                success=False,
                trigger=RollbackTrigger.MANUAL,
                from_model=current_model,
                to_model=fallback_model,
                error_message="Already monitoring. Stop current monitoring first.",
            )

        self.is_monitoring = True
        self.current_model = current_model
        self.fallback_model = fallback_model
        self.monitoring_start_time = datetime.now()

        return RollbackResult(
            success=True,
            trigger=RollbackTrigger.MANUAL,
            from_model=current_model,
            to_model=fallback_model,
            reason="Started monitoring",
        )

    def check_health(
        self, historical_data: List[Any], current_data: List[Any]
    ) -> HealthCheck:
        """
        Check deployment health using performance regression detection.

        Args:
            historical_data: Historical performance data
            current_data: Current performance data

        Returns:
            HealthCheck with assessment results
        """
        self.last_health_check = datetime.now()

        # Check if we have sufficient data
        if not historical_data or not current_data:
            return HealthCheck(
                is_healthy=False,
                triggers_rollback=False,
                has_sufficient_data=False,
                detected_issues=[RollbackTrigger.HEALTH_CHECK_FAILURE],
                timestamp=self.last_health_check,
            )

        # Use performance detector to analyze health
        try:
            # Extract metric name from data (assume all data has same metric name)
            metric_name = (
                historical_data[0].metric_name
                if historical_data
                else "deployment_health"
            )

            regression_result = self.performance_detector.detect_regression(
                historical_data, current_data, metric_name=metric_name
            )

            is_healthy = not regression_result.is_regression
            detected_issues = []

            if regression_result.is_regression:
                detected_issues.append(RollbackTrigger.PERFORMANCE_REGRESSION)

            return HealthCheck(
                is_healthy=is_healthy,
                triggers_rollback=not is_healthy,
                detected_issues=detected_issues,
                has_sufficient_data=True,
                timestamp=self.last_health_check,
                metrics_summary={
                    "p_value": regression_result.p_value,
                    "effect_size": regression_result.effect_size,
                    "is_significant_change": regression_result.is_significant_change,
                },
            )

        except Exception as e:
            return HealthCheck(
                is_healthy=False,
                triggers_rollback=False,
                detected_issues=[RollbackTrigger.HEALTH_CHECK_FAILURE],
                has_sufficient_data=False,
                timestamp=self.last_health_check,
                metrics_summary={"error": str(e)},
            )

    def trigger_automatic_rollback_if_needed(
        self, historical_data: List[Any], current_data: List[Any]
    ) -> Optional[RollbackResult]:
        """
        Check health and trigger automatic rollback if needed.

        Args:
            historical_data: Historical performance data
            current_data: Current performance data

        Returns:
            RollbackResult if rollback was triggered, None otherwise
        """
        if not self.is_monitoring:
            return None

        health = self.check_health(historical_data, current_data)

        if health.triggers_rollback and health.detected_issues:
            # Determine primary trigger
            primary_trigger = health.detected_issues[0]
            reason = f"Automatic rollback triggered by {primary_trigger.value}"

            return self._execute_rollback(primary_trigger, reason)

        return None

    def execute_manual_rollback(self, reason: str) -> RollbackResult:
        """
        Execute manual rollback with specified reason.

        Args:
            reason: Human-readable reason for manual rollback

        Returns:
            RollbackResult with rollback details
        """
        if not self.is_monitoring:
            return RollbackResult(
                success=False,
                trigger=RollbackTrigger.MANUAL,
                from_model="unknown",
                to_model="unknown",
                error_message="Not monitoring any deployment",
            )

        return self._execute_rollback(RollbackTrigger.MANUAL, reason)

    def _execute_rollback(
        self, trigger: RollbackTrigger, reason: str
    ) -> RollbackResult:
        """
        Internal method to execute rollback.

        Args:
            trigger: What triggered the rollback
            reason: Reason for rollback

        Returns:
            RollbackResult with execution details
        """
        start_time = time.time()

        try:
            # Execute rollback through model registry
            rollback_result = self.model_registry.rollback_to_model(self.fallback_model)

            end_time = time.time()
            duration = end_time - start_time

            if rollback_result.success:
                # Record successful rollback
                event = RollbackEvent(
                    trigger=trigger,
                    from_model=self.current_model,
                    to_model=self.fallback_model,
                    success=True,
                    reason=reason,
                    duration=duration,
                    timestamp=datetime.now(),
                )
                self.rollback_history.append(event)

                # Update current state
                self.current_model = self.fallback_model

                return RollbackResult(
                    success=True,
                    trigger=trigger,
                    from_model=event.from_model,
                    to_model=event.to_model,
                    reason=reason,
                    duration=duration,
                )
            else:
                # Record failed rollback
                event = RollbackEvent(
                    trigger=trigger,
                    from_model=self.current_model,
                    to_model=self.fallback_model,
                    success=False,
                    reason=reason,
                    duration=duration,
                    error_message="Model registry rollback failed",
                    timestamp=datetime.now(),
                )
                self.rollback_history.append(event)

                return RollbackResult(
                    success=False,
                    trigger=trigger,
                    from_model=self.current_model,
                    to_model=self.fallback_model,
                    reason=reason,
                    error_message="Model registry rollback failed",
                    duration=duration,
                )

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            error_message = str(e)

            # Record failed rollback
            event = RollbackEvent(
                trigger=trigger,
                from_model=self.current_model,
                to_model=self.fallback_model,
                success=False,
                reason=reason,
                duration=duration,
                error_message=error_message,
                timestamp=datetime.now(),
            )
            self.rollback_history.append(event)

            return RollbackResult(
                success=False,
                trigger=trigger,
                from_model=self.current_model,
                to_model=self.fallback_model,
                reason=reason,
                error_message=error_message,
                duration=duration,
            )

    def stop_monitoring(self) -> None:
        """Stop rollback monitoring."""
        self.is_monitoring = False
        self.current_model = None
        self.fallback_model = None
        self.monitoring_start_time = None

    def get_rollback_status(self) -> RollbackStatus:
        """
        Get current rollback monitoring status.

        Returns:
            RollbackStatus with current state information
        """
        return RollbackStatus(
            is_monitoring=self.is_monitoring,
            current_model=self.current_model,
            fallback_model=self.fallback_model,
            monitoring_start_time=self.monitoring_start_time,
            last_health_check=self.last_health_check,
            rollback_count=len(self.rollback_history),
        )

    def get_rollback_history(self) -> List[RollbackEvent]:
        """
        Get complete rollback history.

        Returns:
            List of RollbackEvent objects in chronological order
        """
        # In production, this would fetch from persistent storage
        return sorted(self.rollback_history, key=lambda x: x.timestamp)

    def export_rollback_history_to_json(self) -> str:
        """
        Export rollback history to JSON format.

        Returns:
            JSON string representation of rollback history
        """
        history_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_rollbacks": len(self.rollback_history),
            "events": [
                {
                    "trigger": event.trigger.value,
                    "from_model": event.from_model,
                    "to_model": event.to_model,
                    "success": event.success,
                    "reason": event.reason,
                    "timestamp": event.timestamp.isoformat(),
                    "duration": event.duration,
                    "error_message": event.error_message,
                }
                for event in self.get_rollback_history()
            ],
        }

        return json.dumps(history_data, indent=2, default=str)
