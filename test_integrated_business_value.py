#!/usr/bin/env python3
"""Test script for the integrated comprehensive business value system."""

import sys

sys.path.append("services/achievement_collector")

from services.achievement_collector.services.business_value_calculator import (
    AgileBusinessValueCalculator,
)


def test_comprehensive_integration():
    """Test the comprehensive business value model integration."""

    calculator = AgileBusinessValueCalculator()

    # Test case 1: Time savings with team detection
    test_pr_1 = {
        "description": """
        ## Summary
        This PR implements automated testing pipeline that **saves 8 hours per week for senior developers** 
        across our **4-person engineering team**, while **eliminating 3 critical production incidents per month** 
        through automated testing and **reducing deployment time by 75%**.
        
        ## Technical Implementation
        - Added comprehensive CI/CD pipeline with automated testing
        - Implemented infrastructure as code with Terraform
        - Built monitoring and alerting system
        """,
        "metrics": {
            "additions": 1200,
            "deletions": 300,
            "files_changed": 15,
            "pr_number": 123,
            "team_size": 4,
            "engineering_team_size": 4,
        },
    }

    # Test case 2: AI/ML system with competitive advantage
    test_pr_2 = {
        "description": """
        ## AI-Powered Business Value System
        
        Built an **AI-powered business value measurement system** that automatically extracts and quantifies 
        financial impact. This **LLM integration** provides **competitive advantage** through **AI automation**.
        
        The system **saves $50,000 annually** in manual analysis work and enables **platform capabilities** 
        for future AI features.
        """,
        "metrics": {
            "additions": 2500,
            "deletions": 400,
            "files_changed": 25,
            "pr_number": 124,
        },
    }

    print("=== Testing Comprehensive Business Value Integration ===\n")

    for i, test_case in enumerate([test_pr_1, test_pr_2], 1):
        print(f"--- Test Case {i} ---")

        # Extract business value
        result = calculator.extract_business_value(
            test_case["description"], test_case["metrics"]
        )

        if result:
            print(f"✅ Business Value Extracted: ${result['total_value']:,}")
            print(f"📊 Method: {result['method']}")
            print(f"🎯 Confidence: {result['confidence']:.1%}")

            # Check for comprehensive model enhancements
            if "elevator_pitch" in result:
                print("🎤 Elevator Pitch Available: ✅")
                print("📈 Startup KPIs Available: ✅")
                print(
                    f"💼 Interview Talking Points: {len(result.get('interview_talking_points', []))} points"
                )

                # Show sample KPIs
                kpis = result.get("startup_kpis", {})
                print(
                    f"   • Development Velocity: +{kpis.get('development_velocity_increase_pct', 0):.1f}%"
                )
                print(
                    f"   • Time to Market: -{kpis.get('time_to_market_reduction_days', 0):.0f} days"
                )
                print(
                    f"   • User Impact: {kpis.get('user_impact_multiplier', 0):.0f}x multiplier"
                )

                # Show sample talking points
                talking_points = result.get("interview_talking_points", [])
                if talking_points:
                    print(f"💡 Sample Talking Point: '{talking_points[0][:100]}...'")

            else:
                print("⚠️  Comprehensive model not available")

        else:
            print("❌ No business value extracted")

        print()


def test_ai_mlops_focused_extraction():
    """Test extraction focused on AI/MLOps scenarios for job applications."""

    calculator = AgileBusinessValueCalculator()

    ai_mlops_scenarios = [
        {
            "title": "LLM Pipeline Optimization",
            "description": "Optimized LLM inference pipeline reducing response time by 60% and saving $25,000 monthly in GPU costs through model quantization and caching strategies.",
            "metrics": {"additions": 800, "deletions": 200, "files_changed": 12},
        },
        {
            "title": "MLOps Automation Platform",
            "description": "Built automated ML model deployment platform that eliminates 40 hours per month of manual DevOps work for our 6-person ML team, enabling continuous deployment of ML models.",
            "metrics": {"additions": 3000, "deletions": 500, "files_changed": 35},
        },
        {
            "title": "AI-Powered Monitoring",
            "description": "Implemented AI-driven anomaly detection preventing 5 critical production incidents monthly, each costing approximately $15,000 in downtime and recovery.",
            "metrics": {"additions": 1500, "deletions": 100, "files_changed": 20},
        },
    ]

    print("=== AI/MLOps Focused Value Extraction ===\n")

    total_annual_value = 0

    for scenario in ai_mlops_scenarios:
        print(f"🤖 {scenario['title']}:")

        result = calculator.extract_business_value(
            scenario["description"], scenario["metrics"]
        )

        if result:
            annual_value = result["total_value"]
            if result.get("period") == "monthly":
                annual_value *= 12
            elif result.get("period") == "one-time":
                annual_value = result["total_value"]  # Keep as-is for one-time

            total_annual_value += annual_value

            print(f"   💰 Value: ${annual_value:,}/year")
            print(f"   📊 Method: {result['method']}")
            print(f"   🎯 Type: {result['type']}")

            # Show business impact for interviews
            if "startup_kpis" in result:
                kpis = result["startup_kpis"]
                improvements = []

                if kpis.get("development_velocity_increase_pct", 0) > 0:
                    improvements.append(
                        f"Velocity +{kpis['development_velocity_increase_pct']:.0f}%"
                    )
                if kpis.get("infrastructure_cost_reduction_pct", 0) > 0:
                    improvements.append(
                        f"Cost -{kpis['infrastructure_cost_reduction_pct']:.0f}%"
                    )
                if kpis.get("incident_reduction_pct", 0) > 0:
                    improvements.append(
                        f"Incidents -{kpis['incident_reduction_pct']:.0f}%"
                    )

                if improvements:
                    print(f"   📈 KPIs: {' | '.join(improvements)}")
        else:
            print("   ❌ No value extracted")

        print()

    print(f"🏆 **Total Portfolio Value**: ${total_annual_value:,}/year")
    print(
        f"🎯 **Average per Project**: ${total_annual_value // len(ai_mlops_scenarios):,}/year"
    )

    if total_annual_value > 500000:
        print(
            "✅ **Interview Ready**: Portfolio value exceeds $500K threshold for senior roles"
        )
    elif total_annual_value > 200000:
        print("⚡ **Strong Portfolio**: Good value demonstration for mid-level roles")
    else:
        print("📈 **Growing Portfolio**: Focus on higher-impact projects")


if __name__ == "__main__":
    test_comprehensive_integration()
    print("\n" + "=" * 60 + "\n")
    test_ai_mlops_focused_extraction()
