#!/usr/bin/env python3
"""Comprehensive test runner for dashboard API tests."""

import sys
import subprocess
import argparse
import time
from pathlib import Path


class DashboardTestRunner:
    """Test runner for dashboard API with multiple test categories."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent / "tests"
        self.project_root = Path(__file__).parent.parent.parent
        self.results = {}
    
    def run_unit_tests(self, verbose=False):
        """Run unit tests."""
        print("\n🧪 Running Unit Tests...")
        
        unit_test_files = [
            "test_variant_metrics_comprehensive.py",
            "test_websocket_comprehensive.py"
        ]
        
        cmd = [
            "python", "-m", "pytest",
            "-v" if verbose else "-q",
            "--tb=short",
            "--durations=10",
            *[str(self.test_dir / f) for f in unit_test_files]
        ]
        
        result = self._run_command(cmd, "Unit Tests")
        self.results["unit"] = result
        return result
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests."""
        print("\n🔗 Running Integration Tests...")
        
        integration_test_files = [
            "test_websocket_integration.py",
            "test_dashboard_integration.py"
        ]
        
        cmd = [
            "python", "-m", "pytest",
            "-v" if verbose else "-q",
            "--tb=short",
            "--durations=10",
            "-m", "not e2e",  # Exclude e2e tests from integration
            *[str(self.test_dir / f) for f in integration_test_files if (self.test_dir / f).exists()]
        ]
        
        result = self._run_command(cmd, "Integration Tests")
        self.results["integration"] = result
        return result
    
    def run_e2e_tests(self, verbose=False):
        """Run end-to-end tests."""
        print("\n🌐 Running End-to-End Tests...")
        
        e2e_test_files = [
            "test_e2e_complete_dashboard.py",
            "test_e2e_dashboard.py"
        ]
        
        cmd = [
            "python", "-m", "pytest",
            "-v" if verbose else "-q",
            "--tb=short",
            "--durations=15",
            "-m", "e2e or asyncio",
            *[str(self.test_dir / f) for f in e2e_test_files if (self.test_dir / f).exists()]
        ]
        
        result = self._run_command(cmd, "End-to-End Tests")
        self.results["e2e"] = result
        return result
    
    def run_performance_tests(self, verbose=False):
        """Run performance tests."""
        print("\n⚡ Running Performance Tests...")
        
        performance_test_files = [
            "test_edge_cases_and_performance.py"
        ]
        
        cmd = [
            "python", "-m", "pytest",
            "-v" if verbose else "-q",
            "--tb=short",
            "--durations=20",
            "-k", "performance or stress or load",
            *[str(self.test_dir / f) for f in performance_test_files if (self.test_dir / f).exists()]
        ]
        
        result = self._run_command(cmd, "Performance Tests")
        self.results["performance"] = result
        return result
    
    def run_edge_case_tests(self, verbose=False):
        """Run edge case tests."""
        print("\n🔥 Running Edge Case Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "-v" if verbose else "-q",
            "--tb=short",
            "--durations=10",
            "-k", "edge_case or malformed or failure",
            str(self.test_dir / "test_edge_cases_and_performance.py")
        ]
        
        result = self._run_command(cmd, "Edge Case Tests")
        self.results["edge_cases"] = result
        return result
    
    def run_frontend_tests(self, verbose=False):
        """Run frontend tests."""
        print("\n⚛️  Running Frontend Tests...")
        
        frontend_dir = self.project_root / "services" / "dashboard_frontend"
        if not frontend_dir.exists():
            print("❌ Frontend directory not found, skipping frontend tests")
            self.results["frontend"] = False
            return False
        
        # Check for package.json and test script
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            print("❌ package.json not found, skipping frontend tests")
            self.results["frontend"] = False
            return False
        
        cmd = ["npm", "test", "--", "--run"]
        result = self._run_command(cmd, "Frontend Tests", cwd=frontend_dir)
        self.results["frontend"] = result
        return result
    
    def run_all_tests(self, verbose=False, skip_frontend=False):
        """Run all test suites."""
        print("🚀 Running Complete Dashboard Test Suite")
        print("=" * 50)
        
        start_time = time.time()
        
        # Run backend tests
        backend_results = [
            self.run_unit_tests(verbose),
            self.run_integration_tests(verbose),
            self.run_e2e_tests(verbose),
            self.run_edge_case_tests(verbose),
            self.run_performance_tests(verbose)
        ]
        
        # Run frontend tests if not skipped
        if not skip_frontend:
            frontend_result = self.run_frontend_tests(verbose)
            backend_results.append(frontend_result)
        
        total_time = time.time() - start_time
        
        # Print summary
        self._print_summary(total_time, skip_frontend)
        
        return all(backend_results)
    
    def run_quick_tests(self, verbose=False):
        """Run a quick subset of tests for rapid feedback."""
        print("⚡ Running Quick Test Suite (Unit + Basic Integration)")
        print("=" * 50)
        
        start_time = time.time()
        
        # Run only unit tests and basic integration
        cmd = [
            "python", "-m", "pytest",
            "-v" if verbose else "-q",
            "--tb=short",
            "-k", "not (performance or stress or e2e)",
            str(self.test_dir)
        ]
        
        result = self._run_command(cmd, "Quick Tests")
        total_time = time.time() - start_time
        
        print(f"\n⏱️  Quick tests completed in {total_time:.2f} seconds")
        print(f"✅ Result: {'PASSED' if result else 'FAILED'}")
        
        return result
    
    def run_coverage_tests(self, verbose=False):
        """Run tests with coverage reporting."""
        print("\n📊 Running Tests with Coverage Analysis...")
        
        cmd = [
            "python", "-m", "pytest",
            "--cov=services.dashboard_api",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
            "-v" if verbose else "-q",
            str(self.test_dir)
        ]
        
        result = self._run_command(cmd, "Coverage Tests")
        
        if result:
            print("\n📈 Coverage report generated in htmlcov/index.html")
        
        return result
    
    def _run_command(self, cmd, test_name, cwd=None):
        """Run a command and return success status."""
        if cwd is None:
            cwd = self.project_root
        
        try:
            print(f"\n▶️  Executing: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=False,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            success = result.returncode == 0
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"\n{status} - {test_name}")
            
            return success
            
        except subprocess.TimeoutExpired:
            print(f"\n⏰ TIMEOUT - {test_name} (exceeded 5 minutes)")
            return False
        except FileNotFoundError:
            print(f"\n❌ COMMAND NOT FOUND - {test_name}")
            print(f"   Command: {' '.join(cmd)}")
            return False
        except Exception as e:
            print(f"\n💥 ERROR - {test_name}: {e}")
            return False
    
    def _print_summary(self, total_time, skip_frontend=False):
        """Print test execution summary."""
        print("\n" + "=" * 50)
        print("📋 TEST EXECUTION SUMMARY")
        print("=" * 50)
        
        for test_type, result in self.results.items():
            if test_type == "frontend" and skip_frontend:
                continue
            
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_type.upper():.<20} {status}")
        
        print(f"\n⏱️  Total execution time: {total_time:.2f} seconds")
        
        all_passed = all(r for r in self.results.values() if not (skip_frontend and "frontend" in str(r)))
        overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
        print(f"\n🎯 Overall Result: {overall_status}")
        
        if not all_passed:
            print("\n💡 To investigate failures:")
            print("   - Run with --verbose for detailed output")
            print("   - Check specific test files for detailed error messages")
            print("   - Use pytest --tb=long for full tracebacks")
    
    def check_dependencies(self):
        """Check if all required dependencies are installed."""
        print("🔍 Checking test dependencies...")
        
        required_packages = [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "httpx",
            "websockets",
            "psutil"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ {package} - MISSING")
                missing_packages.append(package)
        
        if missing_packages:
            print("\n💡 Install missing packages with:")
            print(f"   pip install {' '.join(missing_packages)}")
            return False
        
        print("\n✅ All dependencies are available")
        return True


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Dashboard API Test Runner")
    
    parser.add_argument(
        "test_type",
        nargs="?",
        choices=["unit", "integration", "e2e", "performance", "edge", "frontend", "all", "quick", "coverage"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--skip-frontend",
        action="store_true",
        help="Skip frontend tests"
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check test dependencies and exit"
    )
    
    args = parser.parse_args()
    
    runner = DashboardTestRunner()
    
    if args.check_deps:
        success = runner.check_dependencies()
        sys.exit(0 if success else 1)
    
    # Map test types to methods
    test_methods = {
        "unit": runner.run_unit_tests,
        "integration": runner.run_integration_tests,
        "e2e": runner.run_e2e_tests,
        "performance": runner.run_performance_tests,
        "edge": runner.run_edge_case_tests,
        "frontend": runner.run_frontend_tests,
        "all": lambda v: runner.run_all_tests(v, args.skip_frontend),
        "quick": runner.run_quick_tests,
        "coverage": runner.run_coverage_tests
    }
    
    if args.test_type in test_methods:
        success = test_methods[args.test_type](args.verbose)
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Unknown test type: {args.test_type}")
        sys.exit(1)


if __name__ == "__main__":
    main()
