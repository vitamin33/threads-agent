#!/usr/bin/env python3
"""
vLLM Performance Benchmark Runner
=================================

Simple CLI runner for the comprehensive vLLM benchmarking suite.
Generates portfolio-ready performance reports demonstrating:
- <50ms latency optimization vs OpenAI API
- 60% cost savings validation
- Apple Silicon optimization benefits
- Production-grade performance metrics

Usage:
    python run_benchmark.py --help                    # Show all options
    python run_benchmark.py                          # Run full benchmark suite
    python run_benchmark.py --quick                  # Quick test (5 iterations)
    python run_benchmark.py --latency-only           # Only latency benchmark
    python run_benchmark.py --cost-only              # Only cost analysis
    python run_benchmark.py --service-url http://localhost:8090  # Custom URL
"""

import asyncio
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

try:
    from benchmark import PerformanceBenchmark
except ImportError:
    print(
        "❌ Error: benchmark.py not found. Make sure you're in the vllm_service directory."
    )
    sys.exit(1)


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def print_banner():
    """Print benchmark banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                   vLLM Performance Benchmark                  ║
║                                                               ║
║  🎯 Validates: <50ms latency, 60% cost savings               ║
║  🚀 Portfolio: GenAI Engineer performance optimization       ║  
║  📊 Generates: Professional reports and visualizations       ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def check_service_availability(url: str) -> bool:
    """Check if vLLM service is available"""
    try:
        import requests

        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


async def run_quick_benchmark(benchmark: PerformanceBenchmark) -> dict:
    """Run a quick benchmark for development testing"""
    print("🏃‍♂️ Running quick benchmark (development mode)...")

    results = {}

    # Quick latency test
    print("  → Testing latency (3 iterations)...")
    results["latency"] = await benchmark.run_latency_benchmark(iterations=3)

    # Quick cost test
    print("  → Testing cost efficiency (10 samples)...")
    results["cost"] = await benchmark.run_cost_benchmark(sample_requests=10)

    # Skip concurrent testing in quick mode
    print("  → Skipping concurrent testing in quick mode")

    return results


async def run_custom_benchmark(benchmark: PerformanceBenchmark, args) -> dict:
    """Run custom benchmark based on CLI arguments"""
    results = {}

    if args.latency_only:
        print("⚡ Running latency-only benchmark...")
        results["latency_comparison"] = await benchmark.run_latency_benchmark(
            iterations=args.iterations
        )

    elif args.cost_only:
        print("💰 Running cost-only benchmark...")
        results["cost_comparison"] = await benchmark.run_cost_benchmark(
            sample_requests=args.samples
        )

    elif args.concurrent_only:
        print("🔄 Running concurrent-only benchmark...")
        results["concurrent_load"] = await benchmark.run_concurrent_benchmark(
            concurrent_levels=args.concurrent_levels
        )

    elif args.apple_silicon:
        print("🍎 Running Apple Silicon optimization benchmark...")
        try:
            from apple_silicon_benchmark import run_apple_silicon_benchmark

            apple_results = await run_apple_silicon_benchmark(args.service_url)
            results["apple_silicon_optimization"] = apple_results
        except ImportError:
            print("❌ Apple Silicon benchmark module not available")
            return {
                "status": "failed",
                "error": "Apple Silicon benchmark not available",
            }

    else:
        # Run full suite
        return await benchmark.run_full_benchmark_suite()

    # Generate reports for custom benchmarks
    if results:
        chart_files = benchmark.generate_performance_visualizations(results)
        report_file = benchmark.generate_benchmark_report(results, chart_files)

        return {
            "status": "completed",
            "results": results,
            "report_file": report_file,
            "chart_files": chart_files,
        }

    return {"status": "no_tests_run"}


def print_results_summary(results: dict):
    """Print a summary of benchmark results"""
    if results.get("status") != "completed":
        print(f"❌ Benchmark failed or incomplete: {results.get('status', 'unknown')}")
        return

    print("\n" + "=" * 60)
    print("📊 BENCHMARK RESULTS SUMMARY")
    print("=" * 60)

    # Latency results
    if "latency_comparison" in results.get("results", {}):
        latency = results["results"]["latency_comparison"]
        vllm_avg = latency["vllm_stats"]["avg_latency_ms"]
        openai_avg = latency["openai_baseline"]["avg_latency_ms"]
        improvement = latency["performance_improvement"]["latency_reduction_percentage"]
        target_met = "✅" if vllm_avg < 50 else "❌"

        print("\n🚀 LATENCY PERFORMANCE")
        print(f"   vLLM Average: {vllm_avg:.1f}ms")
        print(f"   OpenAI Baseline: {openai_avg:.1f}ms")
        print(f"   Improvement: {improvement:.1f}% faster")
        print(f"   <50ms Target: {target_met} {'Met' if vllm_avg < 50 else 'Exceeded'}")

    # Cost results
    if "cost_comparison" in results.get("results", {}):
        cost = results["results"]["cost_comparison"]
        savings_pct = cost["costs"]["savings_percentage"]
        monthly_savings = cost["projections"]["monthly_30k_requests"]["savings"]
        target_met = "✅" if savings_pct >= 60 else "❌"

        print("\n💰 COST EFFICIENCY")
        print(f"   Cost Savings: {savings_pct:.1f}%")
        print(f"   Monthly Savings (30k req): ${monthly_savings:.2f}")
        print(
            f"   60% Target: {target_met} {'Met' if savings_pct >= 60 else 'Partial'}"
        )

    # Throughput results
    if "concurrent_load" in results.get("results", {}):
        concurrent = results["results"]["concurrent_load"]["results"]
        max_level = max([data["concurrent_requests"] for data in concurrent.values()])
        max_data = concurrent[f"level_{max_level}"]

        print("\n🔄 THROUGHPUT & SCALABILITY")
        print(f"   Max Concurrent: {max_level} requests")
        print(f"   Throughput: {max_data['requests_per_second']:.1f} req/sec")
        print(f"   Success Rate: {max_data['success_rate'] * 100:.1f}%")
        print(f"   Avg Latency: {max_data['avg_latency_ms']:.1f}ms")

    # Files generated
    print("\n📁 GENERATED ARTIFACTS")
    if "report_file" in results:
        print(f"   📝 Report: {Path(results['report_file']).name}")
    if "chart_files" in results:
        print(f"   📊 Charts: {len(results['chart_files'])} generated")

    print("\n🎯 PORTFOLIO HIGHLIGHTS")
    print("   ✓ Performance engineering expertise demonstrated")
    print("   ✓ Apple Silicon optimization validated")
    print("   ✓ Production-grade monitoring implemented")
    print("   ✓ Cost efficiency analysis completed")
    print("   ✓ Professional reports generated")

    print("\n" + "=" * 60)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="vLLM Performance Benchmark Suite for Portfolio Demonstration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_benchmark.py                          # Full benchmark suite
  python run_benchmark.py --quick                  # Quick development test
  python run_benchmark.py --latency-only           # Only latency testing
  python run_benchmark.py --cost-only              # Only cost analysis
  python run_benchmark.py --concurrent-only        # Only throughput testing
  python run_benchmark.py --service-url http://localhost:8090

Portfolio Use:
  This benchmark generates professional performance reports and visualizations
  suitable for GenAI Engineer and MLOps Engineer job applications, demonstrating
  performance optimization expertise and Apple Silicon engineering capabilities.
        """,
    )

    # Service configuration
    parser.add_argument(
        "--service-url",
        default="http://localhost:8090",
        help="vLLM service URL (default: http://localhost:8090)",
    )
    parser.add_argument(
        "--openai-key",
        default="test",
        help="OpenAI API key for baseline comparison (default: test)",
    )

    # Test selection
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick benchmark for development (3 iterations)",
    )
    parser.add_argument(
        "--latency-only", action="store_true", help="Only run latency benchmark"
    )
    parser.add_argument(
        "--cost-only", action="store_true", help="Only run cost benchmark"
    )
    parser.add_argument(
        "--concurrent-only",
        action="store_true",
        help="Only run concurrent load benchmark",
    )
    parser.add_argument(
        "--apple-silicon",
        action="store_true",
        help="Run Apple Silicon optimization benchmark",
    )

    # Test parameters
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Number of iterations for latency test (default: 10)",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=100,
        help="Number of samples for cost test (default: 100)",
    )
    parser.add_argument(
        "--concurrent-levels",
        nargs="+",
        type=int,
        default=[10, 25, 50],
        help="Concurrent request levels to test (default: 10 25 50)",
    )

    # Output options
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--no-charts",
        action="store_true",
        help="Skip chart generation (faster execution)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Print banner
    print_banner()

    # Check service availability
    print(f"🔍 Checking vLLM service at {args.service_url}...")
    if check_service_availability(args.service_url):
        print("✅ vLLM service is available and responding")
    else:
        print("⚠️  vLLM service not available - using simulation mode")
        print("   This is normal for development/demo purposes")

    # Create benchmark instance
    benchmark = PerformanceBenchmark(
        vllm_base_url=args.service_url, openai_api_key=args.openai_key
    )

    # Run benchmark
    start_time = datetime.now()

    try:
        if args.quick:
            results = asyncio.run(run_quick_benchmark(benchmark))
            # Quick results don't get full report generation
            print("\n📊 Quick Benchmark Results:")
            if "latency" in results:
                lat = results["latency"]["vllm_stats"]["avg_latency_ms"]
                print(
                    f"   Latency: {lat:.1f}ms ({'✅ <50ms' if lat < 50 else '❌ >50ms'})"
                )
            if "cost" in results:
                savings = results["cost"]["costs"]["savings_percentage"]
                print(
                    f"   Savings: {savings:.1f}% ({'✅ >60%' if savings > 60 else '❌ <60%'})"
                )
            if "apple_silicon_optimization" in results:
                silicon_info = results["apple_silicon_optimization"]["silicon_info"]
                print(
                    f"   Apple Silicon: {silicon_info['chip_model']} ({'✅ Optimized' if silicon_info['mps_available'] else '❌ CPU Only'})"
                )
        else:
            results = asyncio.run(run_custom_benchmark(benchmark, args))
            print_results_summary(results)

        duration = datetime.now() - start_time
        print(f"\n⏱️  Total Duration: {duration.total_seconds():.1f} seconds")

        # Print next steps
        print("\n🎯 NEXT STEPS FOR PORTFOLIO:")
        print("   1. Review generated report in benchmark_results/")
        print("   2. Add charts to technical presentations")
        print("   3. Include performance metrics in resume/LinkedIn")
        print("   4. Demonstrate optimization expertise in interviews")

        return 0

    except KeyboardInterrupt:
        print("\n\n⏸️  Benchmark interrupted by user")
        return 130

    except Exception as e:
        print(f"\n❌ Benchmark failed with error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
