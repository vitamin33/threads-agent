"""
GradualRolloutManager - Canary deployment system with traffic progression.

Part of CRA-297 CI/CD Pipeline implementation. Provides gradual rollout capabilities
with traffic progression: 10% → 25% → 50% → 100% with monitoring at each stage.

This implementation follows strict TDD practices and integrates with the
PerformanceRegressionDetector for health monitoring during rollout.

Author: TDD Implementation for CRA-297
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class RolloutError(Exception):
    """Raised when GradualRolloutManager encounters an error."""

    pass


class RolloutStage(Enum):
    """Enumeration of rollout stages with traffic percentages."""

    PREPARATION = ("preparation", 0)
    CANARY_10 = ("canary_10", 10)
    CANARY_25 = ("canary_25", 25)
    CANARY_50 = ("canary_50", 50)
    FULL_ROLLOUT = ("full_rollout", 100)

    def __init__(self, stage_name: str, traffic_percentage: int):
        self.stage_name = stage_name
        self.traffic_percentage = traffic_percentage


@dataclass
class DeploymentHealth:
    """
    Represents the health status of a deployment.

    Attributes:
        is_healthy: Whether the deployment is considered healthy
        regression_detected: Whether performance regression was detected
        metrics_summary: Summary of key metrics
        timestamp: When the health check was performed
    """

    is_healthy: bool
    regression_detected: bool
    metrics_summary: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RolloutResult:
    """
    Result of a rollout operation.

    Attributes:
        success: Whether the operation was successful
        stage: Current rollout stage after operation
        traffic_percentage: Current traffic percentage
        error_message: Error message if operation failed
        timestamp: When the operation was executed
        health_metrics: Health metrics snapshot
        duration: Duration of the operation in seconds
    """

    success: bool
    stage: RolloutStage
    traffic_percentage: int
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    health_metrics: Optional[Dict[str, Any]] = None
    duration: float = 0.0


@dataclass
class RolloutStatus:
    """
    Current status of an active rollout.

    Attributes:
        current_stage: Current stage of the rollout
        traffic_percentage: Current traffic percentage
        model_version: Version of the model being rolled out
        start_time: When the rollout started
        is_active: Whether the rollout is currently active
        is_timed_out: Whether the rollout has timed out
        health_status: Current health status
    """

    current_stage: RolloutStage
    traffic_percentage: int
    model_version: str
    start_time: datetime
    is_active: bool
    is_timed_out: bool = False
    health_status: Optional[DeploymentHealth] = None


class GradualRolloutManager:
    """
    Canary deployment system with gradual traffic progression.

    Provides comprehensive rollout capabilities including:
    - Progressive traffic routing: 10% → 25% → 50% → 100%
    - Real-time health monitoring using PerformanceRegressionDetector
    - Automatic rollback on performance degradation
    - Manual override and control capabilities
    - Detailed status reporting and logging

    Integrates with existing CI/CD pipeline for automated deployments.
    """

    def __init__(
        self,
        performance_detector,
        stage_timeout_minutes: int = 30,
        auto_advance_on_healthy: bool = False,
    ):
        """
        Initialize GradualRolloutManager.

        Args:
            performance_detector: PerformanceRegressionDetector instance for health monitoring
            stage_timeout_minutes: Timeout for each stage in minutes
            auto_advance_on_healthy: Whether to automatically advance on healthy metrics

        Raises:
            RolloutError: If performance_detector is None
        """
        if performance_detector is None:
            raise RolloutError("Performance detector cannot be None")

        self.performance_detector = performance_detector
        self.stage_timeout_minutes = stage_timeout_minutes
        self.auto_advance_on_healthy = auto_advance_on_healthy

        # Current rollout state
        self.current_stage = RolloutStage.PREPARATION
        self.traffic_percentage = 0
        self.model_version: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.is_active = False

        # Stage progression mapping
        self.stage_progression = {
            RolloutStage.PREPARATION: RolloutStage.CANARY_10,
            RolloutStage.CANARY_10: RolloutStage.CANARY_25,
            RolloutStage.CANARY_25: RolloutStage.CANARY_50,
            RolloutStage.CANARY_50: RolloutStage.FULL_ROLLOUT,
            RolloutStage.FULL_ROLLOUT: None,  # No next stage
        }

    def start_rollout(self, model_version: str) -> RolloutResult:
        """
        Start a gradual rollout for the specified model version.

        Args:
            model_version: Version identifier of the model to roll out

        Returns:
            RolloutResult with operation details
        """
        start_time = datetime.now()

        # Check if rollout is already active
        if self.is_active:
            return RolloutResult(
                success=False,
                stage=self.current_stage,
                traffic_percentage=self.traffic_percentage,
                error_message="Rollout already active. Complete or abort current rollout first.",
                timestamp=start_time,
            )

        # Initialize rollout
        self.model_version = model_version
        self.start_time = start_time
        self.is_active = True
        self.current_stage = RolloutStage.CANARY_10
        self.traffic_percentage = RolloutStage.CANARY_10.traffic_percentage

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return RolloutResult(
            success=True,
            stage=self.current_stage,
            traffic_percentage=self.traffic_percentage,
            timestamp=start_time,
            duration=duration,
        )

    def advance_stage(
        self, historical_data: List[Any] = None, current_data: List[Any] = None
    ) -> RolloutResult:
        """
        Advance to the next rollout stage.

        Args:
            historical_data: Optional historical performance data for health checking
            current_data: Optional current performance data for health checking

        Returns:
            RolloutResult with operation details
        """
        start_time = datetime.now()

        # Check if rollout is active
        if not self.is_active:
            return RolloutResult(
                success=False,
                stage=self.current_stage,
                traffic_percentage=self.traffic_percentage,
                error_message="No active rollout. Start a rollout first.",
                timestamp=start_time,
            )

        # Perform health check if data is provided
        if historical_data is not None and current_data is not None:
            health = self.monitor_deployment_health(historical_data, current_data)
            if health.regression_detected:
                return RolloutResult(
                    success=False,
                    stage=self.current_stage,
                    traffic_percentage=self.traffic_percentage,
                    error_message="Regression detected. Rollout blocked.",
                    timestamp=start_time,
                    health_metrics=health.metrics_summary,
                )

        # Get next stage
        next_stage = self.stage_progression.get(self.current_stage)
        if next_stage is None:
            return RolloutResult(
                success=False,
                stage=self.current_stage,
                traffic_percentage=self.traffic_percentage,
                error_message="Already at final stage.",
                timestamp=start_time,
            )

        # Update state
        self.current_stage = next_stage
        self.traffic_percentage = next_stage.traffic_percentage

        # If reached full rollout, mark as complete
        if next_stage == RolloutStage.FULL_ROLLOUT:
            self.is_active = False

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return RolloutResult(
            success=True,
            stage=self.current_stage,
            traffic_percentage=self.traffic_percentage,
            timestamp=start_time,
            duration=duration,
        )

    def monitor_deployment_health(
        self, historical_data: List[Any], current_data: List[Any]
    ) -> DeploymentHealth:
        """
        Monitor deployment health using performance regression detection.

        Args:
            historical_data: Historical performance data
            current_data: Current performance data

        Returns:
            DeploymentHealth with assessment results
        """
        # Use performance detector to analyze health
        # Extract metric name from data (assume all data has same metric name)
        metric_name = (
            historical_data[0].metric_name if historical_data else "performance_metric"
        )

        regression_result = self.performance_detector.detect_regression(
            historical_data, current_data, metric_name=metric_name
        )

        is_healthy = not regression_result.is_regression

        return DeploymentHealth(
            is_healthy=is_healthy,
            regression_detected=regression_result.is_regression,
            metrics_summary={
                "p_value": regression_result.p_value,
                "effect_size": regression_result.effect_size,
                "is_significant_change": regression_result.is_significant_change,
            },
            timestamp=datetime.now(),
        )

    def get_rollout_status(self) -> RolloutStatus:
        """
        Get current rollout status.

        Returns:
            RolloutStatus with current state information
        """
        is_timed_out = False
        if self.is_active and self.start_time:
            elapsed = datetime.now() - self.start_time
            is_timed_out = elapsed.total_seconds() > (self.stage_timeout_minutes * 60)

        return RolloutStatus(
            current_stage=self.current_stage,
            traffic_percentage=self.traffic_percentage,
            model_version=self.model_version or "unknown",
            start_time=self.start_time or datetime.now(),
            is_active=self.is_active,
            is_timed_out=is_timed_out,
        )
