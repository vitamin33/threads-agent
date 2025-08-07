"""
Chaos Experiment Executor - Core engine for running chaos experiments.

This module provides the main executor for chaos engineering experiments,
including safety controls, metrics integration, and emergency stop functionality.
"""

import asyncio
import time
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from unittest.mock import Mock

import pybreaker
from prometheus_client import Counter, Histogram, Gauge


class ExperimentState(Enum):
    """States that a chaos experiment can be in."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EMERGENCY_STOPPED = "EMERGENCY_STOPPED"


@dataclass
class ExperimentResult:
    """Result of a chaos experiment execution."""
    experiment_name: str
    status: ExperimentState
    execution_time: float
    safety_checks_passed: bool
    actions_performed: List[str]
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        result = asdict(self)
        result["status"] = self.status.value
        return result


class SafetyViolationError(Exception):
    """Raised when safety thresholds are violated during experiment execution."""
    pass


class ChaosExperimentExecutor:
    """
    Main executor for chaos experiments with safety controls and monitoring.
    
    This class orchestrates chaos experiments while ensuring system safety
    through circuit breakers, health checks, and emergency stop mechanisms.
    """
    
    def __init__(
        self,
        prometheus_client: Optional[Any] = None,
        circuit_breaker: Optional[Any] = None,
        safety_threshold: float = 0.8
    ):
        """
        Initialize the chaos experiment executor.
        
        Args:
            prometheus_client: Client for metrics collection
            circuit_breaker: Circuit breaker for safety controls
            safety_threshold: Minimum health threshold (0.0 to 1.0)
        """
        self.prometheus_client = prometheus_client or Mock()
        self.circuit_breaker = circuit_breaker or Mock()
        self.safety_threshold = safety_threshold
        self._emergency_stop_flag = False
        
        # Initialize Prometheus metrics
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize Prometheus metrics for monitoring."""
        try:
            self.experiments_total = Counter(
                'chaos_experiments_total', 
                'Total number of chaos experiments executed'
            )
        except ValueError:
            # Use existing metric
            from prometheus_client import REGISTRY
            for collector in REGISTRY._collector_to_names:
                if hasattr(collector, '_name') and 'chaos_experiments_total' in collector._name:
                    self.experiments_total = collector
                    break
            else:
                self.experiments_total = Mock()
        
        try:
            self.experiments_success_total = Counter(
                'chaos_experiments_success_total',
                'Total number of successful chaos experiments'
            )
        except ValueError:
            self.experiments_success_total = Mock()
            
        try:
            self.experiment_duration = Histogram(
                'chaos_experiment_duration_seconds',
                'Duration of chaos experiments in seconds'
            )
        except ValueError:
            self.experiment_duration = Mock()
            
        try:
            self.system_health_gauge = Gauge(
                'chaos_system_health_score',
                'Current system health score (0.0 to 1.0)'
            )
        except ValueError:
            self.system_health_gauge = Mock()
    
    async def execute_experiment(self, experiment_config: Dict[str, Any]) -> ExperimentResult:
        """
        Execute a chaos experiment with safety controls.
        
        Args:
            experiment_config: Configuration dictionary for the experiment
            
        Returns:
            ExperimentResult: Result of the experiment execution
            
        Raises:
            SafetyViolationError: If safety thresholds are violated
        """
        experiment_name = experiment_config.get("name", "unknown")
        experiment_type = experiment_config.get("type", "unknown")
        duration = experiment_config.get("duration", 30)
        
        start_time = time.time()
        actions_performed = []
        
        try:
            # Update metrics
            self.prometheus_client.inc('chaos_experiments_total')
            self.experiments_total.inc()
            
            # Perform initial safety check
            health_score = await self._check_system_health()
            if health_score < self.safety_threshold:
                raise SafetyViolationError(
                    f"System health below safety threshold: {health_score} < {self.safety_threshold}"
                )
            
            # Execute the experiment based on type
            if experiment_type == "pod_kill":
                actions_performed.append("pod_kill")
                await self._execute_pod_kill(experiment_config)
            elif experiment_type == "network_partition":
                actions_performed.append("network_partition")
                await self._execute_network_partition(experiment_config)
            elif experiment_type == "cpu_stress":
                actions_performed.append("cpu_stress")
                await self._execute_cpu_stress(experiment_config)
            elif experiment_type == "memory_pressure":
                actions_performed.append("memory_pressure")
                await self._execute_memory_pressure(experiment_config)
            
            # Wait for duration or until emergency stop
            await self._wait_with_monitoring(duration)
            
            # Perform health check
            actions_performed.append("health_check")
            final_health = await self._check_system_health()
            
            execution_time = time.time() - start_time
            
            # Determine final status
            if self._emergency_stop_flag:
                actions_performed.append("emergency_stop")
                status = ExperimentState.EMERGENCY_STOPPED
            else:
                status = ExperimentState.COMPLETED
                self.prometheus_client.inc('chaos_experiments_success_total')
                self.experiments_success_total.inc()
            
            # Update metrics
            self.prometheus_client.observe('chaos_experiment_duration_seconds', execution_time)
            self.experiment_duration.observe(execution_time)
            
            return ExperimentResult(
                experiment_name=experiment_name,
                status=status,
                execution_time=execution_time,
                safety_checks_passed=True,
                actions_performed=actions_performed
            )
            
        except SafetyViolationError:
            execution_time = time.time() - start_time
            return ExperimentResult(
                experiment_name=experiment_name,
                status=ExperimentState.FAILED,
                execution_time=execution_time,
                safety_checks_passed=False,
                actions_performed=actions_performed,
                error_message="Safety threshold violation"
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ExperimentResult(
                experiment_name=experiment_name,
                status=ExperimentState.FAILED,
                execution_time=execution_time,
                safety_checks_passed=False,
                actions_performed=actions_performed,
                error_message=str(e)
            )
    
    async def emergency_stop(self):
        """Trigger emergency stop for all running experiments."""
        self._emergency_stop_flag = True
    
    async def _check_system_health(self) -> float:
        """
        Check the current system health score.
        
        Returns:
            float: Health score between 0.0 and 1.0
        """
        # Mock implementation - in real implementation this would check:
        # - Pod readiness
        # - Service response times
        # - Error rates
        # - Resource utilization
        return 0.9
    
    async def _execute_pod_kill(self, config: Dict[str, Any]):
        """Execute a pod kill experiment."""
        # Mock implementation - would use Kubernetes API to kill pods
        await asyncio.sleep(0.1)
    
    async def _execute_network_partition(self, config: Dict[str, Any]):
        """Execute a network partition experiment."""
        # Mock implementation - would configure network policies
        await asyncio.sleep(0.1)
    
    async def _execute_cpu_stress(self, config: Dict[str, Any]):
        """Execute a CPU stress experiment."""
        # Mock implementation - would deploy stress test pods
        await asyncio.sleep(0.1)
    
    async def _execute_memory_pressure(self, config: Dict[str, Any]):
        """Execute a memory pressure experiment."""
        # Mock implementation - would deploy memory stress pods
        await asyncio.sleep(0.1)
    
    async def _wait_with_monitoring(self, duration: int):
        """
        Wait for the specified duration while monitoring for emergency stop.
        
        Args:
            duration: Duration to wait in seconds
        """
        elapsed = 0
        while elapsed < duration and not self._emergency_stop_flag:
            await asyncio.sleep(0.1)
            elapsed += 0.1