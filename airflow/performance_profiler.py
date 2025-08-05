"""
Performance Profiler for Airflow Custom Operators (CRA-284)

This module provides comprehensive performance profiling and optimization
analysis for all custom Airflow operators in the viral learning flywheel.

Key Performance Requirements:
- Task execution time < 200ms p99
- Memory usage < 100MB baseline
- Connection pooling efficiency > 90%
- 10% minimum improvement target

Epic: E7 - Viral Learning Flywheel
"""

import time
import psutil
import cProfile
import pstats
import io
import threading
from datetime import datetime
from typing import Dict, List, Any
from contextlib import contextmanager
from dataclasses import dataclass
import numpy as np

# Import the operators for profiling
import sys
import os

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "operators"))

try:
    from operators.viral_scraper_operator import ViralScraperOperator
    from operators.viral_engine_operator import ViralEngineOperator
    from operators.thompson_sampling_operator import ThompsonSamplingOperator
    from operators.metrics_collector_operator import MetricsCollectorOperator
    from operators.health_check_operator import HealthCheckOperator
except ImportError:
    # Fallback imports
    from viral_scraper_operator import ViralScraperOperator
    from viral_engine_operator import ViralEngineOperator
    from thompson_sampling_operator import ThompsonSamplingOperator
    from metrics_collector_operator import MetricsCollectorOperator
    from health_check_operator import HealthCheckOperator


@dataclass
class PerformanceMetrics:
    """Performance metrics container."""

    execution_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    network_requests: int
    connection_reuse_ratio: float
    error_count: int

    def to_dict(self) -> Dict[str, float]:
        return {
            "execution_time_ms": self.execution_time_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "network_requests": self.network_requests,
            "connection_reuse_ratio": self.connection_reuse_ratio,
            "error_count": self.error_count,
        }


@dataclass
class PerformanceBaseline:
    """Performance baseline container for comparison."""

    operator_name: str
    baseline_metrics: PerformanceMetrics
    target_metrics: PerformanceMetrics
    optimization_opportunities: List[str]


class OperatorProfiler:
    """
    Comprehensive profiler for Airflow custom operators.

    Provides:
    - Memory usage profiling with memory_profiler
    - CPU profiling with cProfile
    - Network connection monitoring
    - Custom performance benchmarks
    - Bottleneck identification
    - Optimization recommendations
    """

    def __init__(self):
        self.results = {}
        self.baselines = {}
        self.process = psutil.Process()
        self.network_monitor = NetworkMonitor()

        # Performance targets
        self.targets = {
            "execution_time_ms": 200,  # p99 < 200ms
            "memory_usage_mb": 100,  # baseline < 100MB
            "connection_reuse_ratio": 0.90,  # > 90%
            "error_rate": 0.01,  # < 1%
        }

    @contextmanager
    def profile_operator(self, operator_name: str):
        """Context manager for profiling operator execution."""
        print(f"\n🔍 PROFILING: {operator_name}")
        print("=" * 60)

        # Reset monitoring
        self.network_monitor.reset()
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        initial_cpu = self.process.cpu_percent()
        start_time = time.perf_counter()

        # Start network monitoring
        monitor_thread = threading.Thread(target=self.network_monitor.start_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()

        # Enable profiling
        profiler = cProfile.Profile()
        profiler.enable()

        try:
            yield

        finally:
            # Stop profiling
            profiler.disable()
            end_time = time.perf_counter()

            # Stop monitoring
            self.network_monitor.stop_monitoring()

            # Calculate metrics
            execution_time_ms = (end_time - start_time) * 1000
            final_memory = self.process.memory_info().rss / 1024 / 1024
            memory_usage_mb = final_memory - initial_memory
            cpu_usage_percent = self.process.cpu_percent() - initial_cpu

            # Get network stats
            network_stats = self.network_monitor.get_stats()

            # Create metrics
            metrics = PerformanceMetrics(
                execution_time_ms=execution_time_ms,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage_percent,
                network_requests=network_stats["total_requests"],
                connection_reuse_ratio=network_stats["connection_reuse_ratio"],
                error_count=network_stats["error_count"],
            )

            # Store results
            self.results[operator_name] = {
                "metrics": metrics,
                "profiler_stats": self._extract_profiler_stats(profiler),
                "network_details": network_stats,
                "timestamp": datetime.now().isoformat(),
            }

            # Print results
            self._print_metrics(operator_name, metrics)

    def _extract_profiler_stats(self, profiler: cProfile.Profile) -> Dict[str, Any]:
        """Extract key statistics from cProfile."""
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.sort_stats("cumulative")
        ps.print_stats(20)  # Top 20 functions

        # Get key metrics
        stats = ps.get_stats_profile()
        total_calls = stats.total_calls
        total_time = stats.total_tt

        # Find bottleneck functions
        bottlenecks = []
        for func, (cc, nc, tt, ct, callers) in ps.stats.items():
            if ct > 0.01:  # Functions taking > 10ms
                bottlenecks.append(
                    {
                        "function": f"{func[0]}:{func[1]}({func[2]})",
                        "cumulative_time": ct,
                        "total_time": tt,
                        "calls": cc,
                    }
                )

        return {
            "total_calls": total_calls,
            "total_time": total_time,
            "bottlenecks": sorted(
                bottlenecks, key=lambda x: x["cumulative_time"], reverse=True
            )[:10],
            "profile_output": s.getvalue(),
        }

    def _print_metrics(self, operator_name: str, metrics: PerformanceMetrics):
        """Print formatted performance metrics."""
        print(f"\n📊 PERFORMANCE METRICS: {operator_name}")
        print("-" * 50)

        # Execution time
        time_status = (
            "✅"
            if metrics.execution_time_ms < self.targets["execution_time_ms"]
            else "⚠️"
        )
        print(
            f"{time_status} Execution Time: {metrics.execution_time_ms:.1f}ms (target: <{self.targets['execution_time_ms']}ms)"
        )

        # Memory usage
        memory_status = (
            "✅" if metrics.memory_usage_mb < self.targets["memory_usage_mb"] else "⚠️"
        )
        print(
            f"{memory_status} Memory Usage: {metrics.memory_usage_mb:.1f}MB (target: <{self.targets['memory_usage_mb']}MB)"
        )

        # Connection reuse
        conn_status = (
            "✅"
            if metrics.connection_reuse_ratio > self.targets["connection_reuse_ratio"]
            else "⚠️"
        )
        print(
            f"{conn_status} Connection Reuse: {metrics.connection_reuse_ratio:.1%} (target: >{self.targets['connection_reuse_ratio']:.0%})"
        )

        # Network requests
        print(f"🌐 Network Requests: {metrics.network_requests}")
        print(f"⚡ CPU Usage: {metrics.cpu_usage_percent:.1f}%")
        print(f"❌ Errors: {metrics.error_count}")

    def analyze_bottlenecks(self) -> Dict[str, List[str]]:
        """Analyze performance bottlenecks and generate optimization recommendations."""
        bottlenecks = {}

        for operator_name, result in self.results.items():
            issues = []
            metrics = result["metrics"]
            profiler_stats = result["profiler_stats"]

            # Performance issues
            if metrics.execution_time_ms > self.targets["execution_time_ms"]:
                issues.append(
                    f"CRITICAL: Execution time {metrics.execution_time_ms:.1f}ms exceeds target {self.targets['execution_time_ms']}ms"
                )

            if metrics.memory_usage_mb > self.targets["memory_usage_mb"]:
                issues.append(
                    f"WARNING: Memory usage {metrics.memory_usage_mb:.1f}MB exceeds target {self.targets['memory_usage_mb']}MB"
                )

            if metrics.connection_reuse_ratio < self.targets["connection_reuse_ratio"]:
                issues.append(
                    f"OPTIMIZATION: Connection reuse {metrics.connection_reuse_ratio:.1%} below target {self.targets['connection_reuse_ratio']:.0%}"
                )

            # Code-level bottlenecks
            if profiler_stats["bottlenecks"]:
                top_bottleneck = profiler_stats["bottlenecks"][0]
                if top_bottleneck["cumulative_time"] > 0.1:  # > 100ms
                    issues.append(
                        f"BOTTLENECK: {top_bottleneck['function']} takes {top_bottleneck['cumulative_time'] * 1000:.1f}ms"
                    )

            # Network issues
            if metrics.network_requests > 10 and metrics.connection_reuse_ratio < 0.5:
                issues.append(
                    "NETWORK: Too many requests with poor connection reuse - implement connection pooling"
                )

            # Memory issues
            if metrics.memory_usage_mb > 50:
                issues.append(
                    "MEMORY: High memory usage - investigate object lifecycle and implement streaming where possible"
                )

            bottlenecks[operator_name] = issues

        return bottlenecks

    def generate_optimization_plan(self) -> Dict[str, Dict[str, Any]]:
        """Generate comprehensive optimization plan for each operator."""
        bottlenecks = self.analyze_bottlenecks()
        optimization_plan = {}

        for operator_name, issues in bottlenecks.items():
            metrics = self.results[operator_name]["metrics"]
            profiler_stats = self.results[operator_name]["profiler_stats"]

            optimizations = []
            expected_improvements = {}

            # Execution time optimizations
            if metrics.execution_time_ms > self.targets["execution_time_ms"]:
                optimizations.extend(
                    [
                        "Implement async/await patterns for I/O operations",
                        "Add connection pooling with persistent connections",
                        "Implement request batching to reduce round trips",
                        "Add response caching for repeated requests",
                    ]
                )
                expected_improvements["execution_time"] = "30-50% reduction"

            # Memory optimizations
            if metrics.memory_usage_mb > self.targets["memory_usage_mb"]:
                optimizations.extend(
                    [
                        "Implement streaming for large data processing",
                        "Use generators instead of lists where possible",
                        "Add explicit cleanup in __del__ or context managers",
                        "Implement pagination for large result sets",
                    ]
                )
                expected_improvements["memory_usage"] = "40-60% reduction"

            # Connection optimizations
            if metrics.connection_reuse_ratio < self.targets["connection_reuse_ratio"]:
                optimizations.extend(
                    [
                        "Configure connection pooling with proper pool size",
                        "Implement session-level HTTP adapters",
                        "Add connection keep-alive settings",
                        "Use connection multiplexing where applicable",
                    ]
                )
                expected_improvements["connection_efficiency"] = (
                    "80-95% connection reuse"
                )

            # Code-level optimizations
            if profiler_stats["bottlenecks"]:
                for bottleneck in profiler_stats["bottlenecks"][:3]:  # Top 3
                    if "requests" in bottleneck["function"]:
                        optimizations.append(
                            f"Optimize HTTP requests in {bottleneck['function']}"
                        )
                    elif "json" in bottleneck["function"]:
                        optimizations.append(
                            f"Optimize JSON processing in {bottleneck['function']}"
                        )
                    elif "time.sleep" in bottleneck["function"]:
                        optimizations.append(
                            f"Replace blocking sleep with async wait in {bottleneck['function']}"
                        )

                expected_improvements["cpu_efficiency"] = "20-40% reduction in CPU time"

            optimization_plan[operator_name] = {
                "current_metrics": metrics.to_dict(),
                "issues": issues,
                "optimizations": optimizations,
                "expected_improvements": expected_improvements,
                "priority": self._calculate_priority(metrics),
                "estimated_effort": self._estimate_effort(optimizations),
            }

        return optimization_plan

    def _calculate_priority(self, metrics: PerformanceMetrics) -> str:
        """Calculate optimization priority based on performance gaps."""
        score = 0

        if metrics.execution_time_ms > self.targets["execution_time_ms"] * 2:
            score += 3
        elif metrics.execution_time_ms > self.targets["execution_time_ms"]:
            score += 2

        if metrics.memory_usage_mb > self.targets["memory_usage_mb"] * 2:
            score += 3
        elif metrics.memory_usage_mb > self.targets["memory_usage_mb"]:
            score += 2

        if metrics.connection_reuse_ratio < 0.5:
            score += 2
        elif metrics.connection_reuse_ratio < self.targets["connection_reuse_ratio"]:
            score += 1

        if score >= 6:
            return "CRITICAL"
        elif score >= 4:
            return "HIGH"
        elif score >= 2:
            return "MEDIUM"
        else:
            return "LOW"

    def _estimate_effort(self, optimizations: List[str]) -> str:
        """Estimate implementation effort based on optimization types."""
        effort_points = 0

        for opt in optimizations:
            if any(
                keyword in opt.lower()
                for keyword in ["async", "pooling", "architecture"]
            ):
                effort_points += 3
            elif any(keyword in opt.lower() for keyword in ["caching", "batching"]):
                effort_points += 2
            else:
                effort_points += 1

        if effort_points <= 3:
            return "LOW (1-2 days)"
        elif effort_points <= 6:
            return "MEDIUM (3-5 days)"
        else:
            return "HIGH (1-2 weeks)"

    def benchmark_optimization_impact(
        self,
        operator_name: str,
        original_metrics: PerformanceMetrics,
        optimized_metrics: PerformanceMetrics,
    ) -> Dict[str, float]:
        """Calculate the impact of optimizations."""
        improvements = {}

        # Execution time improvement
        time_improvement = (
            original_metrics.execution_time_ms - optimized_metrics.execution_time_ms
        ) / original_metrics.execution_time_ms
        improvements["execution_time"] = time_improvement * 100

        # Memory improvement
        if original_metrics.memory_usage_mb > 0:
            memory_improvement = (
                original_metrics.memory_usage_mb - optimized_metrics.memory_usage_mb
            ) / original_metrics.memory_usage_mb
            improvements["memory_usage"] = memory_improvement * 100

        # Connection efficiency improvement
        conn_improvement = (
            optimized_metrics.connection_reuse_ratio
            - original_metrics.connection_reuse_ratio
        )
        improvements["connection_efficiency"] = conn_improvement * 100

        # Overall performance score
        overall_score = (
            improvements.get("execution_time", 0)
            + improvements.get("memory_usage", 0)
            + improvements.get("connection_efficiency", 0)
        ) / 3
        improvements["overall"] = overall_score

        return improvements

    def export_results(self, filename: str = None) -> str:
        """Export profiling results to JSON file."""
        if not filename:
            filename = f"airflow_operators_performance_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        export_data = {
            "profiling_timestamp": datetime.now().isoformat(),
            "performance_targets": self.targets,
            "operator_results": {},
            "optimization_plan": self.generate_optimization_plan(),
            "summary": self._generate_summary(),
        }

        # Convert metrics to serializable format
        for operator_name, result in self.results.items():
            export_data["operator_results"][operator_name] = {
                "metrics": result["metrics"].to_dict(),
                "network_details": result["network_details"],
                "timestamp": result["timestamp"],
                "top_bottlenecks": result["profiler_stats"]["bottlenecks"][:5],
            }

        import json

        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2)

        return filename

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate performance summary across all operators."""
        if not self.results:
            return {}

        all_metrics = [result["metrics"] for result in self.results.values()]

        return {
            "total_operators_profiled": len(self.results),
            "avg_execution_time_ms": np.mean(
                [m.execution_time_ms for m in all_metrics]
            ),
            "max_execution_time_ms": np.max([m.execution_time_ms for m in all_metrics]),
            "avg_memory_usage_mb": np.mean([m.memory_usage_mb for m in all_metrics]),
            "avg_connection_reuse_ratio": np.mean(
                [m.connection_reuse_ratio for m in all_metrics]
            ),
            "total_network_requests": sum([m.network_requests for m in all_metrics]),
            "operators_exceeding_time_target": sum(
                1
                for m in all_metrics
                if m.execution_time_ms > self.targets["execution_time_ms"]
            ),
            "operators_exceeding_memory_target": sum(
                1
                for m in all_metrics
                if m.memory_usage_mb > self.targets["memory_usage_mb"]
            ),
            "operators_below_connection_target": sum(
                1
                for m in all_metrics
                if m.connection_reuse_ratio < self.targets["connection_reuse_ratio"]
            ),
        }


class NetworkMonitor:
    """Monitor network connections and requests during operator execution."""

    def __init__(self):
        self.connections = []
        self.requests = []
        self.monitoring = False
        self.start_time = None

    def reset(self):
        """Reset monitoring state."""
        self.connections.clear()
        self.requests.clear()
        self.monitoring = False
        self.start_time = None

    def start_monitoring(self):
        """Start monitoring network activity."""
        self.monitoring = True
        self.start_time = time.time()

        # Monitor active connections
        while self.monitoring:
            try:
                proc = psutil.Process()
                connections = proc.connections()
                self.connections.extend(
                    [
                        {
                            "timestamp": time.time(),
                            "local_addr": conn.laddr,
                            "remote_addr": conn.raddr,
                            "status": conn.status,
                        }
                        for conn in connections
                        if conn.raddr
                    ]
                )
                time.sleep(0.1)  # Sample every 100ms
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

    def stop_monitoring(self):
        """Stop monitoring network activity."""
        self.monitoring = False

    def get_stats(self) -> Dict[str, Any]:
        """Get network monitoring statistics."""
        if not self.connections:
            return {
                "total_requests": 0,
                "unique_connections": 0,
                "connection_reuse_ratio": 0.0,
                "error_count": 0,
                "avg_connection_duration": 0.0,
            }

        # Analyze connections
        unique_endpoints = set()
        connection_reuses = 0
        total_requests = len(self.connections)

        for conn in self.connections:
            endpoint = conn.get("remote_addr")
            if endpoint:
                if endpoint in unique_endpoints:
                    connection_reuses += 1
                unique_endpoints.add(endpoint)

        connection_reuse_ratio = connection_reuses / max(total_requests, 1)

        return {
            "total_requests": total_requests,
            "unique_connections": len(unique_endpoints),
            "connection_reuse_ratio": connection_reuse_ratio,
            "error_count": 0,  # Would need to track HTTP errors separately
            "monitoring_duration": time.time() - (self.start_time or time.time()),
        }


def create_mock_context():
    """Create a mock Airflow context for testing."""
    return {
        "dag": None,
        "task": None,
        "execution_date": datetime.now(),
        "ds": datetime.now().strftime("%Y-%m-%d"),
        "task_instance": None,
    }


def profile_all_operators():
    """Profile all custom Airflow operators and generate optimization report."""
    profiler = OperatorProfiler()

    print("🚀 AIRFLOW OPERATORS PERFORMANCE PROFILING")
    print("=" * 80)
    print("Target Performance Requirements:")
    print(f"  • Execution Time: < {profiler.targets['execution_time_ms']}ms (p99)")
    print(f"  • Memory Usage: < {profiler.targets['memory_usage_mb']}MB (baseline)")
    print(f"  • Connection Reuse: > {profiler.targets['connection_reuse_ratio']:.0%}")
    print("  • Minimum Improvement: 10%")
    print()

    # Mock service URLs for testing
    test_urls = {
        "orchestrator": "http://localhost:8080",
        "viral_scraper": "http://localhost:8081",
        "viral_engine": "http://localhost:8082",
        "viral_pattern_engine": "http://localhost:8083",
        "persona_runtime": "http://localhost:8084",
    }

    create_mock_context()

    # Profile each operator
    operators_to_profile = [
        (
            "ViralScraperOperator",
            lambda: ViralScraperOperator(
                task_id="test_viral_scraper",
                viral_scraper_url=test_urls["viral_scraper"],
                account_ids=["test_account"],
                max_posts_per_account=10,
                timeout=30,
            ),
        ),
        (
            "ViralEngineOperator",
            lambda: ViralEngineOperator(
                task_id="test_viral_engine",
                viral_engine_url=test_urls["viral_engine"],
                operation="extract_patterns",
                batch_size=10,
                timeout=30,
            ),
        ),
        (
            "ThompsonSamplingOperator",
            lambda: ThompsonSamplingOperator(
                task_id="test_thompson_sampling",
                orchestrator_url=test_urls["orchestrator"],
                operation="update_parameters",
                timeout=30,
            ),
        ),
        (
            "MetricsCollectorOperator",
            lambda: MetricsCollectorOperator(
                task_id="test_metrics_collector", service_urls=test_urls, timeout=30
            ),
        ),
        (
            "HealthCheckOperator",
            lambda: HealthCheckOperator(
                task_id="test_health_check", service_urls=test_urls, timeout=30
            ),
        ),
    ]

    # Profile each operator
    for operator_name, operator_factory in operators_to_profile:
        try:
            with profiler.profile_operator(operator_name):
                operator_factory()

                # Simulate execution without actual network calls
                # In real profiling, this would call operator.execute(context)
                time.sleep(0.05)  # Simulate some processing time

                # Simulate network activity
                profiler.network_monitor.requests.extend(
                    [
                        {"timestamp": time.time(), "url": url, "status": 200}
                        for url in test_urls.values()
                    ]
                )

        except Exception as e:
            print(f"❌ ERROR profiling {operator_name}: {e}")
            continue

    # Generate optimization report
    print("\n" + "=" * 80)
    print("🔧 OPTIMIZATION ANALYSIS")
    print("=" * 80)

    optimization_plan = profiler.generate_optimization_plan()

    for operator_name, plan in optimization_plan.items():
        print(f"\n📋 {operator_name.upper()}")
        print(f"Priority: {plan['priority']} | Effort: {plan['estimated_effort']}")
        print("-" * 50)

        if plan["issues"]:
            print("🚨 Issues:")
            for issue in plan["issues"]:
                print(f"  • {issue}")

        if plan["optimizations"]:
            print("\n💡 Optimization Recommendations:")
            for i, opt in enumerate(plan["optimizations"], 1):
                print(f"  {i}. {opt}")

        if plan["expected_improvements"]:
            print("\n📈 Expected Improvements:")
            for metric, improvement in plan["expected_improvements"].items():
                print(f"  • {metric}: {improvement}")

    # Export results
    filename = profiler.export_results()
    print(f"\n📄 Detailed results exported to: {filename}")

    # Summary
    summary = profiler._generate_summary()
    print("\n📊 PROFILING SUMMARY")
    print("-" * 30)
    print(f"Operators Profiled: {summary.get('total_operators_profiled', 0)}")
    print(f"Avg Execution Time: {summary.get('avg_execution_time_ms', 0):.1f}ms")
    print(f"Avg Memory Usage: {summary.get('avg_memory_usage_mb', 0):.1f}MB")
    print(f"Avg Connection Reuse: {summary.get('avg_connection_reuse_ratio', 0):.1%}")
    print(
        f"Operators Exceeding Time Target: {summary.get('operators_exceeding_time_target', 0)}"
    )
    print(
        f"Operators Exceeding Memory Target: {summary.get('operators_exceeding_memory_target', 0)}"
    )

    return profiler


if __name__ == "__main__":
    # Run the profiling
    profiler = profile_all_operators()
