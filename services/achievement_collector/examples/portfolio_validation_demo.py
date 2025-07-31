#!/usr/bin/env python3
"""Demo script for Portfolio Value Validation & Metrics Generation."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.portfolio_validator import PortfolioValidator


def main():
    """Demonstrate portfolio validation functionality."""
    # Initialize validator
    validator = PortfolioValidator()

    # Sample achievements data
    achievements = [
        {
            "pr_number": 123,
            "title": "Implement Kubernetes Auto-scaling",
            "description": "Automated infrastructure scaling based on load",
            "business_value": {
                "time_saved_hours": 300,  # $45,000
                "cost_reduction": 80000,  # $80,000
                "revenue_impact": 0,
            },
            "category": "infrastructure",
            "date": "2024-01-15",
        },
        {
            "pr_number": 124,
            "title": "Database Query Optimization",
            "description": "Reduced query times by 70%",
            "business_value": {
                "time_saved_hours": 200,  # $30,000
                "cost_reduction": 50000,  # $50,000
                "revenue_impact": 25000,  # $25,000
            },
            "category": "performance",
            "date": "2024-02-20",
        },
        {
            "pr_number": 125,
            "title": "Security Vulnerability Patching",
            "description": "Fixed critical security vulnerabilities",
            "business_value": {
                "time_saved_hours": 150,  # $22,500
                "cost_reduction": 40000,  # $40,000
                "revenue_impact": 0,
            },
            "category": "security",
            "date": "2024-03-10",
        },
    ]

    print("=== Portfolio Value Validation Demo ===\n")

    # 1. Calculate portfolio value
    print("1. Calculating Portfolio Value...")
    value_result = validator.calculate_portfolio_value(achievements)
    print(f"   Total Value: ${value_result['total_value']:,.0f}")
    print(
        f"   Confidence Interval: ${value_result['confidence_interval']['low']:,.0f} - ${value_result['confidence_interval']['high']:,.0f}\n"
    )

    # 2. Validate against benchmarks
    print("2. Validating Against Industry Benchmarks...")
    validation = validator.validate_against_benchmarks(achievements)
    print(f"   Validation Status: {validation['validation_status'].upper()}")
    for category, data in validation["benchmark_comparison"].items():
        print(
            f"   - {category.title()}: ${data['achievement_value']:,.0f} (Benchmark Avg: ${data['benchmark_avg']:,.0f})"
        )
    print()

    # 3. Generate comprehensive report
    print("3. Generating Comprehensive Report...")
    report = validator.generate_portfolio_report(achievements)
    print(f"   {report['executive_summary']}\n")

    # 4. Calculate statistical confidence
    print("4. Statistical Analysis...")
    stats = validator.calculate_statistical_confidence(achievements)
    print(f"   Mean Achievement Value: ${stats['mean_value']:,.0f}")
    print(f"   Standard Deviation: ${stats['std_deviation']:,.0f}")
    print(
        f"   95% Confidence Interval: ${stats['confidence_interval_95']['low']:,.0f} - ${stats['confidence_interval_95']['high']:,.0f}"
    )
    print(f"   Sample Size: {stats['sample_size']}\n")

    # 5. Export options
    print("5. Export Options Available:")
    print("   - JSON format for APIs and data integration")
    print("   - HTML format for executive presentations")
    print("   - PDF format for formal documentation (requires additional libraries)\n")

    # Save exports
    with open("portfolio_report.json", "w") as f:
        f.write(validator.export_to_json(report))
    print("   ✓ Saved portfolio_report.json")

    with open("portfolio_report.html", "w") as f:
        f.write(validator.export_to_html(report))
    print("   ✓ Saved portfolio_report.html")

    print("\n=== Demo Complete ===")
    print(
        f"\nYour portfolio demonstrates ${value_result['total_value']:,.0f} in quantifiable business value!"
    )
    print(
        "This positions you well within the target range of $200K-$350K for senior MLOps/AI roles."
    )


if __name__ == "__main__":
    main()
