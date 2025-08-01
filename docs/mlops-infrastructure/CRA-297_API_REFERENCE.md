# CRA-297 CI/CD Pipeline API Reference

## Table of Contents

1. [PromptTestRunner](#prompttestrunner)
2. [PerformanceRegressionDetector](#performanceregressiondetector)
3. [GradualRolloutManager](#gradualrolloutmanager)
4. [RollbackController](#rollbackcontroller)
5. [Integration Examples](#integration-examples)
6. [Error Handling](#error-handling)

---

## PromptTestRunner

The `PromptTestRunner` class provides comprehensive testing capabilities for prompt templates.

### Class Definition

```python
from services.common.prompt_test_runner import PromptTestRunner

runner = PromptTestRunner(
    verbose: bool = False,
    parallel: bool = True,
    max_workers: int = 4
)
```

### Methods

#### `run_tests()`

Executes comprehensive tests on a prompt template.

```python
def run_tests(
    self,
    prompt_template: str,
    test_cases: List[Dict[str, Any]],
    validation_rules: Optional[List[str]] = None,
    timeout: int = 30,
    performance_threshold: Optional[Dict[str, float]] = None
) -> Dict[str, Any]
```

**Parameters:**
- `prompt_template` (str): The template string with placeholders (e.g., `{variable}`)
- `test_cases` (List[Dict]): List of test cases with variable values
- `validation_rules` (List[str], optional): Validation rules to apply. Default: all rules
- `timeout` (int): Maximum execution time in seconds. Default: 30
- `performance_threshold` (Dict[str, float], optional): Performance thresholds to check

**Returns:**
```python
{
    "passed": bool,
    "total_tests": int,
    "passed_tests": int,
    "failed_tests": int,
    "validation_results": {
        "template_variables": {"passed": bool, "details": str},
        "min_length": {"passed": bool, "details": str},
        "max_length": {"passed": bool, "details": str},
        "no_profanity": {"passed": bool, "details": str},
        "sql_injection": {"passed": bool, "details": str},
        "prompt_injection": {"passed": bool, "details": str}
    },
    "performance_metrics": {
        "total_execution_time": float,
        "average_test_time": float,
        "memory_usage_mb": float,
        "cpu_usage_percent": float
    },
    "test_case_results": [
        {
            "case_index": int,
            "input": dict,
            "output": str,
            "passed": bool,
            "execution_time": float
        }
    ],
    "errors": List[str]
}
```

**Example:**
```python
runner = PromptTestRunner()
results = runner.run_tests(
    prompt_template="Write a {tone} article about {topic} for {audience}",
    test_cases=[
        {
            "tone": "professional",
            "topic": "AI ethics",
            "audience": "business leaders"
        },
        {
            "tone": "casual",
            "topic": "machine learning",
            "audience": "students"
        }
    ],
    validation_rules=["template_variables", "min_length", "no_profanity"]
)

if results["passed"]:
    print(f"✅ All tests passed! Avg time: {results['performance_metrics']['average_test_time']:.2f}s")
else:
    print(f"❌ {results['failed_tests']} tests failed")
```

#### `validate_template_syntax()`

Validates the syntax of a prompt template.

```python
def validate_template_syntax(
    self,
    template: str
) -> Tuple[bool, List[str], List[str]]
```

**Returns:** Tuple of (is_valid, variables_found, error_messages)

#### `run_performance_benchmark()`

Runs performance benchmarks on a template.

```python
def run_performance_benchmark(
    self,
    template: str,
    test_cases: List[Dict[str, Any]],
    iterations: int = 100
) -> Dict[str, float]
```

**Returns:** Dictionary with performance metrics

---

## PerformanceRegressionDetector

Statistical analysis engine for detecting performance regressions.

### Class Definition

```python
from services.common.performance_regression_detector import PerformanceRegressionDetector

detector = PerformanceRegressionDetector(
    confidence_level: float = 0.95,
    min_effect_size: float = 0.5,
    outlier_threshold: float = 3.0
)
```

### Methods

#### `detect_regression()`

Detects performance regression using statistical tests.

```python
def detect_regression(
    self,
    baseline_values: List[float],
    current_values: List[float],
    metric_name: str = "metric",
    use_statistical_tests: Optional[List[str]] = None,
    consider_direction: str = "both"
) -> Dict[str, Any]
```

**Parameters:**
- `baseline_values` (List[float]): Historical baseline measurements
- `current_values` (List[float]): Current measurements to compare
- `metric_name` (str): Name of the metric being analyzed
- `use_statistical_tests` (List[str], optional): Tests to use. Default: ["t_test", "mann_whitney"]
- `consider_direction` (str): Direction to consider ("increase", "decrease", "both")

**Returns:**
```python
{
    "regression_detected": bool,
    "confidence": float,
    "p_value": float,
    "effect_size": float,
    "statistical_tests": {
        "t_test": {
            "statistic": float,
            "p_value": float,
            "significant": bool
        },
        "mann_whitney": {
            "statistic": float,
            "p_value": float,
            "significant": bool
        }
    },
    "summary_statistics": {
        "baseline": {
            "mean": float,
            "std": float,
            "median": float,
            "min": float,
            "max": float
        },
        "current": {
            "mean": float,
            "std": float,
            "median": float,
            "min": float,
            "max": float
        }
    },
    "confidence_interval": {
        "lower": float,
        "upper": float
    },
    "recommendation": str
}
```

**Example:**
```python
detector = PerformanceRegressionDetector(confidence_level=0.99)

# Detect latency regression
result = detector.detect_regression(
    baseline_values=[95, 98, 92, 96, 94, 97, 93, 95],
    current_values=[105, 108, 103, 107, 104, 106, 102, 105],
    metric_name="response_latency_ms",
    consider_direction="increase"  # Only flag if latency increased
)

if result["regression_detected"]:
    print(f"⚠️ Regression detected! Latency increased by {result['summary_statistics']['current']['mean'] - result['summary_statistics']['baseline']['mean']:.1f}ms")
    print(f"   Confidence: {result['confidence']*100:.1f}%")
    print(f"   Effect size: {result['effect_size']:.2f} (Cohen's d)")
```

#### `calculate_trend()`

Analyzes trend in metrics over time.

```python
def calculate_trend(
    self,
    values: List[float],
    timestamps: Optional[List[float]] = None
) -> Dict[str, Any]
```

**Returns:** Trend analysis with slope, R², and prediction

#### `compare_distributions()`

Compares two distributions for significant differences.

```python
def compare_distributions(
    self,
    dist1: List[float],
    dist2: List[float]
) -> Dict[str, Any]
```

---

## GradualRolloutManager

Manages progressive deployments with automatic health checks.

### Class Definition

```python
from services.common.gradual_rollout_manager import GradualRolloutManager

manager = GradualRolloutManager(
    deployment_name: str,
    prometheus_url: Optional[str] = None,
    health_check_interval: int = 30,
    stage_duration: int = 300  # 5 minutes per stage
)
```

### Methods

#### `start_rollout()`

Initiates a gradual rollout for a new version.

```python
def start_rollout(
    self,
    new_version: str,
    initial_percentage: int = 10,
    stages: Optional[List[int]] = None,
    health_metrics: Optional[List[str]] = None
) -> Dict[str, Any]
```

**Parameters:**
- `new_version` (str): Version identifier for the new deployment
- `initial_percentage` (int): Starting traffic percentage. Default: 10
- `stages` (List[int], optional): Custom stage percentages. Default: [10, 25, 50, 100]
- `health_metrics` (List[str], optional): Metrics to monitor for health checks

**Returns:**
```python
{
    "rollout_id": str,
    "deployment_name": str,
    "new_version": str,
    "current_stage": int,
    "current_percentage": int,
    "stages": List[int],
    "start_time": str,
    "status": str,  # "in_progress", "completed", "failed", "rolled_back"
    "health_status": {
        "healthy": bool,
        "metrics": Dict[str, float],
        "last_check": str
    }
}
```

**Example:**
```python
manager = GradualRolloutManager(
    deployment_name="viral-hook-generator",
    prometheus_url="http://prometheus:9090"
)

# Start rollout with custom stages
rollout = manager.start_rollout(
    new_version="2.1.0",
    initial_percentage=5,  # Start with just 5%
    stages=[5, 10, 25, 50, 75, 100],  # More gradual
    health_metrics=["error_rate", "latency_p95", "engagement_rate"]
)

print(f"Rollout started: {rollout['rollout_id']}")
print(f"Current traffic: {rollout['current_percentage']}%")
```

#### `update_traffic_percentage()`

Updates the traffic distribution.

```python
def update_traffic_percentage(
    self,
    percentage: int,
    force: bool = False
) -> Dict[str, Any]
```

**Parameters:**
- `percentage` (int): New traffic percentage (0-100)
- `force` (bool): Skip health checks if True

#### `get_rollout_status()`

Gets current rollout status and metrics.

```python
def get_rollout_status(self) -> Dict[str, Any]
```

#### `complete_rollout()`

Completes the rollout, sending 100% traffic to new version.

```python
def complete_rollout(
    self,
    skip_final_checks: bool = False
) -> Dict[str, Any]
```

#### `pause_rollout()`

Pauses the rollout at current percentage.

```python
def pause_rollout(
    self,
    reason: str = "Manual pause"
) -> Dict[str, Any]
```

---

## RollbackController

Handles emergency and automatic rollbacks with SLA compliance.

### Class Definition

```python
from services.common.rollback_controller import RollbackController

controller = RollbackController(
    mlflow_client: Optional[MlflowClient] = None,
    model_registry_client: Optional[Any] = None,
    rollback_timeout: int = 30,
    health_check_interval: int = 5
)
```

### Methods

#### `trigger_rollback()`

Executes an immediate rollback.

```python
def trigger_rollback(
    self,
    model_name: str,
    current_version: str,
    target_version: Optional[str] = None,
    reason: str = "Performance regression detected",
    triggered_by: str = "system",
    skip_validation: bool = False
) -> Dict[str, Any]
```

**Parameters:**
- `model_name` (str): Name of the model to rollback
- `current_version` (str): Current deployed version
- `target_version` (str, optional): Specific version to rollback to. If None, uses previous stable
- `reason` (str): Reason for the rollback
- `triggered_by` (str): User or system that triggered rollback
- `skip_validation` (bool): Skip pre-rollback validation if True

**Returns:**
```python
{
    "rollback_id": str,
    "model_name": str,
    "from_version": str,
    "to_version": str,
    "start_time": str,
    "end_time": str,
    "duration_seconds": float,
    "status": str,  # "success", "failed", "timeout"
    "health_check_results": {
        "pre_rollback": Dict[str, Any],
        "post_rollback": Dict[str, Any]
    },
    "reason": str,
    "triggered_by": str,
    "sla_met": bool,  # True if completed < 30s
    "error": Optional[str]
}
```

**Example:**
```python
controller = RollbackController()

# Trigger emergency rollback
result = controller.trigger_rollback(
    model_name="content-generator",
    current_version="3.2.1",
    reason="Critical error rate spike detected",
    triggered_by="monitoring-system"
)

if result["status"] == "success":
    print(f"✅ Rollback completed in {result['duration_seconds']:.1f}s")
    print(f"   SLA {'✅ MET' if result['sla_met'] else '❌ BREACHED'}")
else:
    print(f"❌ Rollback failed: {result['error']}")
```

#### `get_rollback_history()`

Retrieves rollback history for a model.

```python
def get_rollback_history(
    self,
    model_name: str,
    limit: int = 10,
    include_metrics: bool = True
) -> List[Dict[str, Any]]
```

**Returns:** List of rollback events with details

#### `validate_rollback_target()`

Validates if a rollback target version is safe.

```python
def validate_rollback_target(
    self,
    model_name: str,
    target_version: str
) -> Tuple[bool, Optional[str]]
```

**Returns:** Tuple of (is_valid, error_message)

#### `monitor_post_rollback_health()`

Monitors system health after rollback.

```python
def monitor_post_rollback_health(
    self,
    model_name: str,
    duration_seconds: int = 120,
    check_interval: int = 10
) -> Dict[str, Any]
```

---

## Integration Examples

### Complete CI/CD Pipeline Integration

```python
from services.common.prompt_test_runner import PromptTestRunner
from services.common.performance_regression_detector import PerformanceRegressionDetector
from services.common.gradual_rollout_manager import GradualRolloutManager
from services.common.rollback_controller import RollbackController

class CICDPipeline:
    def __init__(self):
        self.test_runner = PromptTestRunner()
        self.regression_detector = PerformanceRegressionDetector()
        self.rollout_manager = GradualRolloutManager("prompt-model")
        self.rollback_controller = RollbackController()
    
    def deploy_new_prompt(self, template: str, version: str):
        # 1. Test the prompt
        test_results = self.test_runner.run_tests(
            prompt_template=template,
            test_cases=self.generate_test_cases(),
            validation_rules=["all"]
        )
        
        if not test_results["passed"]:
            raise ValueError(f"Tests failed: {test_results['errors']}")
        
        # 2. Check for performance regression
        baseline_perf = self.get_baseline_performance()
        current_perf = test_results["performance_metrics"]["average_test_time"]
        
        regression = self.regression_detector.detect_regression(
            baseline_values=baseline_perf,
            current_values=[current_perf] * len(baseline_perf),
            metric_name="execution_time"
        )
        
        if regression["regression_detected"]:
            raise ValueError(f"Performance regression detected: {regression['recommendation']}")
        
        # 3. Start gradual rollout
        rollout = self.rollout_manager.start_rollout(
            new_version=version,
            initial_percentage=10
        )
        
        # 4. Monitor and progress through stages
        for stage in [25, 50, 100]:
            # Wait and monitor
            time.sleep(300)  # 5 minutes
            
            # Check health
            status = self.rollout_manager.get_rollout_status()
            if not status["health_status"]["healthy"]:
                # Trigger rollback
                self.rollback_controller.trigger_rollback(
                    model_name="prompt-model",
                    current_version=version,
                    reason="Health check failed during rollout"
                )
                raise RuntimeError("Deployment failed, rolled back")
            
            # Progress to next stage
            self.rollout_manager.update_traffic_percentage(stage)
        
        return {"status": "success", "version": version}
```

### Async Integration Example

```python
import asyncio
from typing import List, Dict, Any

class AsyncCICDPipeline:
    async def run_parallel_tests(
        self,
        templates: List[str]
    ) -> List[Dict[str, Any]]:
        """Run tests on multiple templates in parallel."""
        tasks = []
        for template in templates:
            task = asyncio.create_task(
                self.test_single_template(template)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def test_single_template(
        self,
        template: str
    ) -> Dict[str, Any]:
        """Test a single template asynchronously."""
        runner = PromptTestRunner()
        loop = asyncio.get_event_loop()
        
        # Run CPU-bound testing in thread pool
        result = await loop.run_in_executor(
            None,
            runner.run_tests,
            template,
            self.generate_test_cases()
        )
        
        return result
```

---

## Error Handling

### Exception Types

```python
# Custom exceptions
class PromptValidationError(Exception):
    """Raised when prompt validation fails."""
    pass

class RegressionDetectedError(Exception):
    """Raised when performance regression is detected."""
    pass

class RolloutError(Exception):
    """Raised when rollout fails."""
    pass

class RollbackTimeoutError(Exception):
    """Raised when rollback exceeds SLA."""
    pass
```

### Error Handling Patterns

```python
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

@contextmanager
def safe_rollback():
    """Context manager for safe rollback operations."""
    controller = RollbackController()
    try:
        yield controller
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        # Always attempt rollback on failure
        try:
            controller.trigger_rollback(
                model_name="current_model",
                current_version="current_version",
                reason=f"Automatic rollback due to: {str(e)}",
                skip_validation=True  # Emergency mode
            )
        except Exception as rollback_error:
            logger.critical(f"Rollback also failed: {rollback_error}")
            # Alert on-call team
            raise RollbackTimeoutError("Critical: Manual intervention required")

# Usage
with safe_rollback() as controller:
    # Risky deployment operation
    deploy_new_model()
```

### Retry Strategies

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class ResilientDeployment:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def deploy_with_retry(self, model_name: str, version: str):
        """Deploy with automatic retry on failure."""
        try:
            return self._deploy(model_name, version)
        except RolloutError as e:
            logger.warning(f"Deployment attempt failed: {e}")
            raise
    
    def _deploy(self, model_name: str, version: str):
        # Actual deployment logic
        pass
```

---

## Performance Considerations

### Resource Limits

```python
# Recommended resource limits for components
RESOURCE_LIMITS = {
    "prompt_test_runner": {
        "max_concurrent_tests": 10,
        "timeout_per_test": 30,
        "memory_limit_mb": 512
    },
    "regression_detector": {
        "max_sample_size": 10000,
        "computation_timeout": 5
    },
    "rollout_manager": {
        "max_concurrent_deployments": 3,
        "health_check_timeout": 10
    },
    "rollback_controller": {
        "max_rollback_time": 30,
        "parallel_operations": 5
    }
}
```

### Optimization Tips

1. **Batch Operations**
```python
# Instead of individual tests
for template in templates:
    runner.run_tests(template, cases)

# Use batch processing
runner.run_batch_tests(templates, cases, max_parallel=10)
```

2. **Cache Results**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_baseline_metrics(model_name: str) -> List[float]:
    # Expensive operation cached
    return fetch_from_prometheus(model_name)
```

3. **Use Connection Pooling**
```python
# For MLflow and Prometheus connections
from urllib3 import PoolManager

http = PoolManager(
    num_pools=10,
    maxsize=20,
    retries=3
)
```

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-31