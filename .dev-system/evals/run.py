"""
M2: Evaluation Runner for Golden Set Testing
Runs evaluation suites and integrates with M1 telemetry for comprehensive testing
"""

import time
import yaml
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

from ops.telemetry import telemetry_decorator


@dataclass
class TestResult:
    """Single test result"""

    test_id: str
    success: bool
    score: float
    latency_ms: float
    cost_usd: float
    error: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SuiteResult:
    """Complete evaluation suite result"""

    suite_name: str
    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    avg_latency_ms: float
    total_cost_usd: float
    weighted_score: float
    gate_status: str  # "PASS", "FAIL", "WARNING"
    test_results: List[TestResult]


class EvaluationRunner:
    """Runs golden set evaluations with telemetry integration"""

    def __init__(self, suite_path: Path):
        self.suite_path = suite_path
        self.suite_config = self._load_suite()

    def _load_suite(self) -> Dict[str, Any]:
        """Load evaluation suite configuration"""
        with open(self.suite_path) as f:
            return yaml.safe_load(f)

    @telemetry_decorator(agent_name="evaluation_runner", event_type="eval_suite")
    def run_suite(self) -> SuiteResult:
        """Run complete evaluation suite"""
        print(f"🧪 Running evaluation suite: {self.suite_config['metadata']['name']}")
        print(f"📋 Agent: {self.suite_config['metadata']['agent']}")
        print(f"🎯 Tests: {len(self.suite_config['test_cases'])}")

        test_results = []
        start_time = time.time()

        for test_case in self.suite_config["test_cases"]:
            result = self._run_test_case(test_case)
            test_results.append(result)

            # Print real-time status
            status = "✅" if result.success else "❌"
            print(
                f"  {status} {result.test_id}: {result.score:.2f} ({result.latency_ms:.0f}ms)"
            )

        total_time = time.time() - start_time

        # Calculate suite metrics
        passed_tests = sum(1 for r in test_results if r.success)
        failed_tests = len(test_results) - passed_tests
        success_rate = passed_tests / len(test_results) if test_results else 0

        avg_latency = (
            sum(r.latency_ms for r in test_results) / len(test_results)
            if test_results
            else 0
        )
        total_cost = sum(r.cost_usd for r in test_results)

        # Calculate weighted score
        weighted_score = self._calculate_weighted_score(test_results)

        # Determine gate status
        gate_status = self._evaluate_gates(
            success_rate, avg_latency, total_cost, weighted_score
        )

        suite_result = SuiteResult(
            suite_name=self.suite_config["metadata"]["name"],
            timestamp=datetime.now().isoformat(),
            total_tests=len(test_results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            success_rate=success_rate,
            avg_latency_ms=avg_latency,
            total_cost_usd=total_cost,
            weighted_score=weighted_score,
            gate_status=gate_status,
            test_results=test_results,
        )

        self._print_suite_summary(suite_result, total_time)
        return suite_result

    @telemetry_decorator(agent_name="evaluation_runner", event_type="test_case")
    def _run_test_case(self, test_case: Dict[str, Any]) -> TestResult:
        """Run a single test case"""
        test_id = test_case["id"]
        weight = test_case.get("weight", 5)

        start_time = time.time()

        try:
            # Mock test execution (replace with actual agent calls)
            result = self._execute_test_case(test_case)

            latency_ms = (time.time() - start_time) * 1000
            score = self._score_test_result(test_case, result)

            return TestResult(
                test_id=test_id,
                success=True,
                score=score,
                latency_ms=latency_ms,
                cost_usd=result.get("cost", 0.0),
                output=result,
                metadata={"weight": weight},
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            # Check if this is an expected error (test should pass)
            expected_output = test_case.get("expected_output", {})
            if "error" in expected_output:
                expected_error = expected_output["error"]
                if expected_error in str(e):
                    # This is an expected error - test passes!
                    return TestResult(
                        test_id=test_id,
                        success=True,  # Expected error = success
                        score=1.0,  # Full score for expected behavior
                        latency_ms=latency_ms,
                        cost_usd=0.0,
                        output={"error": str(e), "expected": True},
                        metadata={"weight": weight, "expected_error": True},
                    )

            # Unexpected error - actual failure
            return TestResult(
                test_id=test_id,
                success=False,
                score=0.0,
                latency_ms=latency_ms,
                cost_usd=0.0,
                error=str(e),
                metadata={"weight": weight},
            )

    def _execute_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test case against target agent (mock implementation)"""
        # This is a mock implementation - replace with actual agent integration

        test_input = test_case.get("input", {})
        expected = test_case.get("expected_output", {})

        # Simulate different test scenarios
        if test_case["id"] == "empty_prompt_handling":
            raise ValueError("invalid_input")

        if test_case["id"] == "malformed_request":
            raise ValueError("invalid_request")

        # Simulate realistic response times
        if "fast" in test_case["id"]:
            time.sleep(0.1)  # Fast operation
        else:
            time.sleep(0.5)  # Normal operation

        # Mock realistic results
        return {
            "content": f"Generated content for {test_input.get('prompt', 'test')}",
            "engagement_score": 0.75,
            "tokens_used": {"input": 50, "output": 100},
            "cost": 0.02,
            "has_hook": True,
            "quality_score": 0.85,
            "should_publish": True,
        }

    def _score_test_result(
        self, test_case: Dict[str, Any], result: Dict[str, Any]
    ) -> float:
        """Score test result against expected criteria"""
        expected = test_case.get("expected_output", {})
        score = 0.0
        max_score = 0.0

        # Check contains requirements
        if "contains" in expected and "content" in result:
            for keyword in expected["contains"]:
                max_score += 1
                if keyword.lower() in result["content"].lower():
                    score += 1

        # Check engagement score
        if "engagement_score" in expected:
            max_score += 2
            actual_score = result.get("engagement_score", 0)
            if actual_score >= expected["engagement_score"]:
                score += 2
            elif actual_score >= expected["engagement_score"] * 0.8:
                score += 1

        # Check quality requirements
        if "has_hook" in expected:
            max_score += 1
            if result.get("has_hook") == expected["has_hook"]:
                score += 1

        # Check content length
        if "min_length" in expected and "content" in result:
            max_score += 1
            if len(result["content"]) >= expected["min_length"]:
                score += 1

        if "max_length" in expected and "content" in result:
            max_score += 1
            if len(result["content"]) <= expected["max_length"]:
                score += 1

        # Return normalized score (0.0 to 1.0)
        return score / max_score if max_score > 0 else 0.0

    def _calculate_weighted_score(self, test_results: List[TestResult]) -> float:
        """Calculate weighted average score across all tests"""
        if not test_results:
            return 0.0

        total_weighted_score = 0.0
        total_weight = 0.0

        for result in test_results:
            weight = result.metadata.get("weight", 5) if result.metadata else 5
            total_weighted_score += result.score * weight
            total_weight += weight

        return total_weighted_score / total_weight if total_weight > 0 else 0.0

    def _evaluate_gates(
        self,
        success_rate: float,
        avg_latency: float,
        total_cost: float,
        weighted_score: float,
    ) -> str:
        """Evaluate quality gates"""
        gates = self.suite_config.get("gates", {})

        failures = []
        warnings = []

        # Check success rate
        min_success = gates.get("min_success_rate", 0.85)
        if success_rate < min_success:
            failures.append(f"Success rate {success_rate:.2f} < {min_success}")
        elif success_rate < min_success + 0.05:
            warnings.append(f"Success rate {success_rate:.2f} close to threshold")

        # Check latency
        max_latency = gates.get("max_avg_latency_ms", 5000)
        if avg_latency > max_latency:
            failures.append(f"Avg latency {avg_latency:.0f}ms > {max_latency}ms")
        elif avg_latency > max_latency * 0.8:
            warnings.append(f"Avg latency {avg_latency:.0f}ms approaching limit")

        # Check cost
        max_cost = gates.get("max_total_cost", 10.0)
        if total_cost > max_cost:
            failures.append(f"Total cost ${total_cost:.2f} > ${max_cost}")
        elif total_cost > max_cost * 0.8:
            warnings.append(f"Total cost ${total_cost:.2f} approaching limit")

        # Check weighted score
        min_score = gates.get("min_weighted_score", 0.85)
        if weighted_score < min_score:
            failures.append(f"Weighted score {weighted_score:.2f} < {min_score}")
        elif weighted_score < min_score + 0.05:
            warnings.append(f"Weighted score {weighted_score:.2f} close to threshold")

        if failures:
            return "FAIL"
        elif warnings:
            return "WARNING"
        else:
            return "PASS"

    def _print_suite_summary(self, result: SuiteResult, total_time: float):
        """Print comprehensive suite summary"""
        print(f"\n{'=' * 60}")
        print(f"📊 Evaluation Summary: {result.suite_name}")
        print(f"{'=' * 60}")
        print(f"Tests:           {result.passed_tests}/{result.total_tests} passed")
        print(f"Success Rate:    {result.success_rate:.1%}")
        print(f"Avg Latency:     {result.avg_latency_ms:.0f}ms")
        print(f"Total Cost:      ${result.total_cost_usd:.3f}")
        print(f"Weighted Score:  {result.weighted_score:.2f}")
        print(f"Execution Time:  {total_time:.1f}s")
        print(f"Gate Status:     {result.gate_status}")

        if result.gate_status == "FAIL":
            print("\n❌ QUALITY GATES FAILED - PR should be blocked")
        elif result.gate_status == "WARNING":
            print("\n⚠️  Quality warnings detected")
        else:
            print("\n✅ All quality gates passed")

    def save_results(self, result: SuiteResult, output_path: Optional[Path] = None):
        """Save evaluation results to file"""
        if output_path is None:
            reports_dir = DEV_SYSTEM_ROOT / "evals" / "reports"
            reports_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = reports_dir / f"eval_{result.suite_name}_{timestamp}.json"

        # Convert dataclasses to dict for JSON serialization
        result_dict = asdict(result)

        with open(output_path, "w") as f:
            json.dump(result_dict, f, indent=2, default=str)

        print(f"💾 Results saved to: {output_path}")
        return output_path


def run_evaluation_suite(suite_name: str = "core") -> SuiteResult:
    """Run evaluation suite by name"""
    suite_path = DEV_SYSTEM_ROOT / "evals" / "suites" / f"{suite_name}.yaml"

    if not suite_path.exists():
        raise FileNotFoundError(f"Evaluation suite not found: {suite_path}")

    runner = EvaluationRunner(suite_path)
    result = runner.run_suite()

    # Save results
    runner.save_results(result)

    return result


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Run golden set evaluations")
    parser.add_argument("--suite", default="core", help="Evaluation suite name")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument(
        "--exit-code", action="store_true", help="Exit with non-zero code if gates fail"
    )

    args = parser.parse_args()

    try:
        result = run_evaluation_suite(args.suite)

        if args.output:
            runner = EvaluationRunner(
                DEV_SYSTEM_ROOT / "evals" / "suites" / f"{args.suite}.yaml"
            )
            runner.save_results(result, Path(args.output))

        # Exit with appropriate code for CI
        if args.exit_code and result.gate_status == "FAIL":
            print("\n❌ Exiting with code 1 due to gate failures")
            sys.exit(1)
        elif args.exit_code and result.gate_status == "WARNING":
            print("\n⚠️  Exiting with code 0 (warnings are non-blocking)")

        print("\n✅ Evaluation complete")

    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        if args.exit_code:
            sys.exit(1)


if __name__ == "__main__":
    main()
