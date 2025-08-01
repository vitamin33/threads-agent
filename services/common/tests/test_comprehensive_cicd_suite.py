"""
Comprehensive CI/CD Pipeline Test Suite Runner - Master test orchestrator.

This suite:
- Orchestrates all CI/CD component tests
- Provides test coverage analysis and reporting
- Implements test categorization and filtering
- Generates comprehensive test reports
- Validates SLA compliance across all components
- Provides performance benchmarking and analysis

Author: Test Generation Specialist for CRA-297
"""

import pytest
import time
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import subprocess
import coverage


@dataclass
class TestSuiteMetrics:
    """Metrics for test suite execution."""
    suite_name: str
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    execution_time: float = 0.0
    coverage_percentage: float = 0.0
    performance_sla_met: bool = True
    error_details: List[str] = field(default_factory=list)


@dataclass
class CICDPipelineTestReport:
    """Comprehensive test report for CI/CD pipeline."""
    timestamp: datetime
    total_execution_time: float
    overall_success_rate: float
    coverage_percentage: float
    sla_compliance: bool
    suite_metrics: List[TestSuiteMetrics] = field(default_factory=list)
    performance_benchmarks: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class CICDTestSuiteOrchestrator:
    """Orchestrates comprehensive testing of all CI/CD pipeline components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize test suite orchestrator."""
        self.config = config or self._get_default_config()
        self.test_suites = self._discover_test_suites()
        self.results: List[TestSuiteMetrics] = []
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for test execution."""
        return {
            'coverage_target': 95.0,
            'performance_sla': {
                'prompt_test_runner': {'max_execution_time': 30.0, 'min_throughput': 50},
                'performance_detector': {'max_detection_time': 5.0, 'max_memory_mb': 500},
                'rollout_manager': {'max_stage_advance_time': 10.0, 'max_rollout_time': 120.0},
                'rollback_controller': {'max_rollback_time': 30.0, 'min_health_check_rate': 60}
            },
            'test_categories': {
                'unit': {'pattern': '**/test_*.py', 'timeout': 300},
                'integration': {'pattern': '**/test_*_integration.py', 'timeout': 600},
                'performance': {'pattern': '**/test_*_performance*.py', 'timeout': 900},
                'advanced': {'pattern': '**/test_*_advanced.py', 'timeout': 600},
                'failure': {'pattern': '**/test_*_failure*.py', 'timeout': 450}
            },
            'parallel_execution': True,
            'fail_fast': False,
            'generate_reports': True
        }
    
    def _discover_test_suites(self) -> Dict[str, List[Path]]:
        """Discover all test suites by category."""
        test_dir = Path(__file__).parent
        suites = {}
        
        for category, config in self.config['test_categories'].items():
            pattern = config['pattern']
            suites[category] = list(test_dir.glob(pattern))
        
        return suites
    
    def run_comprehensive_test_suite(self) -> CICDPipelineTestReport:
        """Run comprehensive test suite for all CI/CD components."""
        print("🚀 Starting Comprehensive CI/CD Pipeline Test Suite")
        print("=" * 80)
        
        overall_start_time = time.time()
        all_suite_metrics = []
        
        # Run tests by category
        for category, test_files in self.test_suites.items():
            if not test_files:
                continue
                
            print(f"\\n📋 Running {category.upper()} Tests")
            print("-" * 40)
            
            category_metrics = self._run_test_category(category, test_files)
            all_suite_metrics.extend(category_metrics)
        
        # Generate overall metrics
        total_execution_time = time.time() - overall_start_time
        overall_metrics = self._calculate_overall_metrics(all_suite_metrics, total_execution_time)
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report(overall_metrics, all_suite_metrics)
        
        # Save report if configured
        if self.config['generate_reports']:
            self._save_report(report)
        
        # Print summary
        self._print_test_summary(report)
        
        return report
    
    def _run_test_category(self, category: str, test_files: List[Path]) -> List[TestSuiteMetrics]:
        """Run tests for a specific category."""
        category_config = self.config['test_categories'][category]
        category_metrics = []
        
        for test_file in test_files:
            print(f"  🧪 {test_file.name}")
            
            suite_start_time = time.time()
            
            # Run individual test suite
            metrics = self._run_individual_test_suite(
                test_file, 
                timeout=category_config['timeout'],
                category=category
            )
            
            metrics.execution_time = time.time() - suite_start_time
            category_metrics.append(metrics)
            
            # Print immediate results
            status = "✅ PASS" if metrics.failed_tests == 0 else "❌ FAIL"
            print(f"    {status} - {metrics.passed_tests}/{metrics.total_tests} tests passed "
                  f"({metrics.execution_time:.2f}s)")
            
            if metrics.failed_tests > 0:
                for error in metrics.error_details[:3]:  # Show first 3 errors
                    print(f"      ⚠️  {error}")
                if len(metrics.error_details) > 3:
                    print(f"      ... and {len(metrics.error_details) - 3} more errors")
        
        return category_metrics
    
    def _run_individual_test_suite(self, test_file: Path, timeout: int, category: str) -> TestSuiteMetrics:
        """Run an individual test suite and collect metrics."""
        suite_name = test_file.stem
        
        try:
            # Prepare pytest command
            cmd = [
                sys.executable, '-m', 'pytest',
                str(test_file),
                '-v',
                '--tb=short',
                '--timeout', str(timeout),
                '--json-report',
                '--json-report-file', f'/tmp/pytest_report_{suite_name}.json'
            ]
            
            # Add coverage if configured
            if category in ['unit', 'integration']:
                cmd.extend([
                    '--cov=services.common',
                    '--cov-report=json:/tmp/coverage_report_{}.json'.format(suite_name)
                ])
            
            # Execute tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 60  # Add buffer to subprocess timeout
            )
            
            # Parse results
            metrics = self._parse_test_results(suite_name, result, test_file)
            
            # Add performance validation
            self._validate_performance_sla(metrics, category)
            
            return metrics
            
        except subprocess.TimeoutExpired:
            return TestSuiteMetrics(
                suite_name=suite_name,
                total_tests=0,
                failed_tests=1,
                execution_time=timeout,
                performance_sla_met=False,
                error_details=[f"Test suite timed out after {timeout}s"]
            )
        except Exception as e:
            return TestSuiteMetrics(
                suite_name=suite_name,
                total_tests=0,
                failed_tests=1,
                execution_time=0.0,
                performance_sla_met=False,
                error_details=[f"Test execution error: {str(e)}"]
            )
    
    def _parse_test_results(self, suite_name: str, result: subprocess.CompletedProcess, test_file: Path) -> TestSuiteMetrics:
        """Parse pytest results and extract metrics."""
        metrics = TestSuiteMetrics(suite_name=suite_name)
        
        try:
            # Parse JSON report if available
            json_report_path = f'/tmp/pytest_report_{suite_name}.json'
            if os.path.exists(json_report_path):
                with open(json_report_path, 'r') as f:
                    json_report = json.load(f)
                
                summary = json_report.get('summary', {})
                metrics.total_tests = summary.get('total', 0)
                metrics.passed_tests = summary.get('passed', 0)
                metrics.failed_tests = summary.get('failed', 0)
                metrics.skipped_tests = summary.get('skipped', 0)
                
                # Extract error details
                for test in json_report.get('tests', []):
                    if test.get('outcome') != 'passed':
                        call_info = test.get('call', {})
                        if 'longrepr' in call_info:
                            error_msg = call_info['longrepr'].split('\\n')[0][:100]
                            metrics.error_details.append(f"{test['nodeid']}: {error_msg}")
            
            # Parse coverage report if available
            coverage_report_path = f'/tmp/coverage_report_{suite_name}.json'
            if os.path.exists(coverage_report_path):
                with open(coverage_report_path, 'r') as f:
                    coverage_report = json.load(f)
                
                metrics.coverage_percentage = coverage_report.get('totals', {}).get('percent_covered', 0.0)
            
            # Fallback to stdout parsing if JSON not available
            if metrics.total_tests == 0:
                self._parse_stdout_results(metrics, result.stdout)
                
        except Exception as e:
            metrics.error_details.append(f"Result parsing error: {str(e)}")
        
        return metrics
    
    def _parse_stdout_results(self, metrics: TestSuiteMetrics, stdout: str) -> None:
        """Parse pytest stdout for basic metrics."""
        lines = stdout.split('\\n')
        
        for line in lines:
            if 'passed' in line and 'failed' in line:
                # Parse line like: "5 passed, 2 failed, 1 skipped in 10.5s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'passed':
                        metrics.passed_tests = int(parts[i-1])
                    elif part == 'failed':
                        metrics.failed_tests = int(parts[i-1])
                    elif part == 'skipped':
                        metrics.skipped_tests = int(parts[i-1])
                
                metrics.total_tests = metrics.passed_tests + metrics.failed_tests + metrics.skipped_tests
                break
    
    def _validate_performance_sla(self, metrics: TestSuiteMetrics, category: str) -> None:
        """Validate performance SLAs for the test suite."""
        if category not in ['performance']:
            return
        
        # Extract component from suite name
        component = None
        for comp in ['prompt_test_runner', 'performance_detector', 'rollout_manager', 'rollback_controller']:
            if comp in metrics.suite_name:
                component = comp
                break
        
        if not component:
            return
        
        sla_config = self.config['performance_sla'].get(component, {})
        
        # Check execution time SLA
        max_execution_time = sla_config.get('max_execution_time')
        if max_execution_time and metrics.execution_time > max_execution_time:
            metrics.performance_sla_met = False
            metrics.error_details.append(
                f"Execution time {metrics.execution_time:.2f}s exceeds SLA {max_execution_time}s"
            )
    
    def _calculate_overall_metrics(self, all_metrics: List[TestSuiteMetrics], total_time: float) -> Dict[str, Any]:
        """Calculate overall metrics across all test suites."""
        total_tests = sum(m.total_tests for m in all_metrics)
        total_passed = sum(m.passed_tests for m in all_metrics)
        total_failed = sum(m.failed_tests for m in all_metrics)
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Calculate average coverage
        coverage_metrics = [m for m in all_metrics if m.coverage_percentage > 0]
        avg_coverage = (sum(m.coverage_percentage for m in coverage_metrics) / len(coverage_metrics)) if coverage_metrics else 0
        
        # Check SLA compliance
        sla_compliance = all(m.performance_sla_met for m in all_metrics)
        
        return {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'success_rate': success_rate,
            'average_coverage': avg_coverage,
            'total_execution_time': total_time,
            'sla_compliance': sla_compliance
        }
    
    def _generate_comprehensive_report(self, overall_metrics: Dict[str, Any], suite_metrics: List[TestSuiteMetrics]) -> CICDPipelineTestReport:
        """Generate comprehensive test report."""
        # Performance benchmarks
        benchmarks = {}
        for category in self.config['test_categories']:
            category_suites = [m for m in suite_metrics if category in m.suite_name]
            if category_suites:
                avg_time = sum(m.execution_time for m in category_suites) / len(category_suites)
                benchmarks[f'{category}_avg_execution_time'] = avg_time
        
        # Generate recommendations
        recommendations = self._generate_recommendations(overall_metrics, suite_metrics)
        
        return CICDPipelineTestReport(
            timestamp=datetime.now(),
            total_execution_time=overall_metrics['total_execution_time'],
            overall_success_rate=overall_metrics['success_rate'],
            coverage_percentage=overall_metrics['average_coverage'],
            sla_compliance=overall_metrics['sla_compliance'],
            suite_metrics=suite_metrics,
            performance_benchmarks=benchmarks,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, overall_metrics: Dict[str, Any], suite_metrics: List[TestSuiteMetrics]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Coverage recommendations
        if overall_metrics['average_coverage'] < self.config['coverage_target']:
            recommendations.append(
                f"Increase test coverage from {overall_metrics['average_coverage']:.1f}% to {self.config['coverage_target']}%"
            )
        
        # Performance recommendations
        slow_suites = [m for m in suite_metrics if m.execution_time > 60]
        if slow_suites:
            recommendations.append(
                f"Optimize {len(slow_suites)} slow test suites (execution time > 60s)"
            )
        
        # Failure recommendations
        if overall_metrics['total_failed'] > 0:
            recommendations.append(
                f"Fix {overall_metrics['total_failed']} failing tests for production readiness"
            )
        
        # SLA recommendations
        if not overall_metrics['sla_compliance']:
            sla_violations = [m for m in suite_metrics if not m.performance_sla_met]
            recommendations.append(
                f"Address SLA violations in {len(sla_violations)} test suites"
            )
        
        return recommendations
    
    def _save_report(self, report: CICDPipelineTestReport) -> None:
        """Save comprehensive test report to file."""
        report_dir = Path('test_reports')
        report_dir.mkdir(exist_ok=True)
        
        timestamp_str = report.timestamp.strftime('%Y%m%d_%H%M%S')
        
        # Save JSON report
        json_report_file = report_dir / f'cicd_test_report_{timestamp_str}.json'
        with open(json_report_file, 'w') as f:
            json.dump({
                'timestamp': report.timestamp.isoformat(),
                'total_execution_time': report.total_execution_time,
                'overall_success_rate': report.overall_success_rate,
                'coverage_percentage': report.coverage_percentage,
                'sla_compliance': report.sla_compliance,
                'suite_metrics': [
                    {
                        'suite_name': m.suite_name,
                        'total_tests': m.total_tests,
                        'passed_tests': m.passed_tests,
                        'failed_tests': m.failed_tests,
                        'execution_time': m.execution_time,
                        'coverage_percentage': m.coverage_percentage,
                        'performance_sla_met': m.performance_sla_met,
                        'error_count': len(m.error_details)
                    }
                    for m in report.suite_metrics
                ],
                'performance_benchmarks': report.performance_benchmarks,
                'recommendations': report.recommendations
            }, f, indent=2)
        
        print(f"\\n📊 Detailed report saved to: {json_report_file}")
    
    def _print_test_summary(self, report: CICDPipelineTestReport) -> None:
        """Print comprehensive test summary."""
        print("\\n" + "=" * 80)
        print("🎯 CI/CD PIPELINE TEST SUMMARY")
        print("=" * 80)
        
        # Overall metrics
        total_tests = sum(m.total_tests for m in report.suite_metrics)
        total_passed = sum(m.passed_tests for m in report.suite_metrics)
        total_failed = sum(m.failed_tests for m in report.suite_metrics)
        
        print(f"📈 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed} ({report.overall_success_rate:.1f}%)")
        print(f"   Failed: {total_failed}")
        print(f"   Execution Time: {report.total_execution_time:.2f}s")
        print(f"   Coverage: {report.coverage_percentage:.1f}%")
        print(f"   SLA Compliance: {'✅ PASS' if report.sla_compliance else '❌ FAIL'}")
        
        # Performance benchmarks
        if report.performance_benchmarks:
            print(f"\\n⚡ Performance Benchmarks:")
            for benchmark, value in report.performance_benchmarks.items():
                print(f"   {benchmark}: {value:.2f}s")
        
        # Category breakdown
        print(f"\\n📋 Test Category Breakdown:")
        categories = {}
        for metric in report.suite_metrics:
            category = self._get_suite_category(metric.suite_name)
            if category not in categories:
                categories[category] = {'total': 0, 'passed': 0, 'failed': 0, 'avg_time': 0}
            categories[category]['total'] += metric.total_tests
            categories[category]['passed'] += metric.passed_tests
            categories[category]['failed'] += metric.failed_tests
        
        for category, stats in categories.items():
            success_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"   {category.upper()}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Recommendations
        if report.recommendations:
            print(f"\\n💡 Recommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"   {i}. {rec}")
        
        # Final status
        print("\\n" + "=" * 80)
        if report.overall_success_rate >= 95 and report.sla_compliance:
            print("🎉 CI/CD PIPELINE: PRODUCTION READY ✅")
        elif report.overall_success_rate >= 90:
            print("⚠️  CI/CD PIPELINE: NEEDS ATTENTION 🟡")
        else:
            print("🚨 CI/CD PIPELINE: NOT PRODUCTION READY ❌")
        print("=" * 80)
    
    def _get_suite_category(self, suite_name: str) -> str:
        """Determine test suite category from name."""
        if 'integration' in suite_name:
            return 'integration'
        elif 'performance' in suite_name or 'sla' in suite_name:
            return 'performance'
        elif 'advanced' in suite_name:
            return 'advanced'
        elif 'failure' in suite_name:
            return 'failure'
        else:
            return 'unit'


class TestComprehensiveCICDSuite:
    """Main test class for running comprehensive CI/CD tests."""
    
    def test_run_comprehensive_cicd_pipeline_tests(self):
        """Run comprehensive CI/CD pipeline test suite."""
        orchestrator = CICDTestSuiteOrchestrator()
        report = orchestrator.run_comprehensive_test_suite()
        
        # Assert overall success criteria
        assert report.overall_success_rate >= 95.0, \
            f"Overall success rate {report.overall_success_rate:.1f}% below 95% threshold"
        
        assert report.coverage_percentage >= 90.0, \
            f"Coverage {report.coverage_percentage:.1f}% below 90% threshold"
        
        assert report.sla_compliance, \
            "SLA compliance requirements not met"
        
        assert report.total_execution_time < 1800, \
            f"Total execution time {report.total_execution_time:.2f}s exceeds 30-minute limit"
        
        # Component-specific assertions
        component_metrics = {}
        for metric in report.suite_metrics:
            component = self._extract_component_name(metric.suite_name)
            if component not in component_metrics:
                component_metrics[component] = []
            component_metrics[component].append(metric)
        
        # Validate each component has comprehensive coverage
        required_components = ['prompt_test_runner', 'performance_regression_detector', 
                             'gradual_rollout_manager', 'rollback_controller']
        
        for component in required_components:
            assert component in component_metrics, f"Missing tests for {component}"
            
            comp_metrics = component_metrics[component]
            total_tests = sum(m.total_tests for m in comp_metrics)
            passed_tests = sum(m.passed_tests for m in comp_metrics)
            
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            assert success_rate >= 95.0, \
                f"{component} success rate {success_rate:.1f}% below 95% threshold"
            
            assert total_tests >= 50, \
                f"{component} has insufficient test coverage: {total_tests} tests"
    
    def _extract_component_name(self, suite_name: str) -> str:
        """Extract component name from test suite name."""
        if 'prompt_test_runner' in suite_name:
            return 'prompt_test_runner'
        elif 'performance_regression_detector' in suite_name:
            return 'performance_regression_detector'
        elif 'gradual_rollout_manager' in suite_name:
            return 'gradual_rollout_manager'
        elif 'rollback_controller' in suite_name:
            return 'rollback_controller'
        else:
            return 'integration'


@pytest.mark.comprehensive
def test_cicd_pipeline_production_readiness():
    """Master test to validate CI/CD pipeline production readiness."""
    print("\\n🚀 VALIDATING CI/CD PIPELINE PRODUCTION READINESS")
    print("=" * 80)
    
    orchestrator = CICDTestSuiteOrchestrator({
        'coverage_target': 95.0,
        'performance_sla': {
            'prompt_test_runner': {'max_execution_time': 30.0},
            'performance_detector': {'max_detection_time': 5.0},
            'rollout_manager': {'max_rollout_time': 120.0},
            'rollback_controller': {'max_rollback_time': 30.0}
        },
        'fail_fast': False,
        'generate_reports': True
    })
    
    report = orchestrator.run_comprehensive_test_suite()
    
    # Production readiness criteria
    production_ready = (
        report.overall_success_rate >= 95.0 and
        report.coverage_percentage >= 95.0 and
        report.sla_compliance and
        len(report.recommendations) <= 2
    )
    
    if production_ready:
        print("\\n🎉 CI/CD PIPELINE IS PRODUCTION READY! 🎉")
    else:
        print("\\n⚠️  CI/CD PIPELINE NEEDS IMPROVEMENTS BEFORE PRODUCTION")
        
        if report.recommendations:
            print("\\nRequired improvements:")
            for rec in report.recommendations:
                print(f"  - {rec}")
    
    assert production_ready, "CI/CD Pipeline not ready for production deployment"


if __name__ == "__main__":
    # Run comprehensive test suite
    test_cicd_pipeline_production_readiness()