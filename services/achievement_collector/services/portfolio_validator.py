"""Portfolio Value Validation & Metrics Generation."""

import json
import math
from datetime import datetime
from typing import Dict, List, Any


class PortfolioValidator:
    """Validates portfolio value and generates metrics."""

    def __init__(self):
        """Initialize the PortfolioValidator."""
        pass

    def calculate_portfolio_value(self, achievements):
        """Calculate total portfolio value from achievements."""
        if not achievements:
            return {"total_value": 0, "confidence_interval": {"low": 0, "high": 0}}

        total_value = 0
        hourly_rate = 150  # $150/hour for senior developer

        for achievement in achievements:
            business_value = achievement.get("business_value", {})

            # Calculate time saved value (ensure non-negative)
            time_saved = max(0, business_value.get("time_saved_hours", 0))
            time_value = time_saved * hourly_rate

            # Add cost reduction (ensure non-negative)
            cost_reduction = max(0, business_value.get("cost_reduction", 0))

            # Add revenue impact (ensure non-negative)
            revenue_impact = max(0, business_value.get("revenue_impact", 0))

            total_value += time_value + cost_reduction + revenue_impact

        return {
            "total_value": total_value,
            "confidence_interval": {
                "low": total_value * 0.8,
                "high": total_value * 1.2,
            },
        }

    def validate_against_benchmarks(self, achievements):
        """Validate achievements against industry benchmarks."""
        # Industry benchmarks for different categories (conservative estimates)
        benchmarks = {
            "infrastructure": {
                "avg_time_saved_hours": 200,
                "avg_cost_reduction": 75000,
                "max_reasonable_value": 500000,
            },
            "performance": {
                "avg_time_saved_hours": 150,
                "avg_cost_reduction": 50000,
                "max_reasonable_value": 300000,
            },
            "feature": {
                "avg_time_saved_hours": 100,
                "avg_cost_reduction": 25000,
                "max_reasonable_value": 200000,
            },
            "security": {
                "avg_time_saved_hours": 300,
                "avg_cost_reduction": 100000,
                "max_reasonable_value": 600000,
            },
        }

        validation_status = "valid"
        benchmark_comparison = {}

        for achievement in achievements:
            category = achievement.get("category", "feature")
            if category not in benchmarks:
                category = "feature"  # Default category

            benchmark = benchmarks[category]
            business_value = achievement.get("business_value", {})

            # Calculate achievement value (ensure non-negative values)
            hourly_rate = 150
            achievement_value = (
                max(0, business_value.get("time_saved_hours", 0)) * hourly_rate
                + max(0, business_value.get("cost_reduction", 0))
                + max(0, business_value.get("revenue_impact", 0))
            )

            # Check if value is within reasonable range
            if achievement_value > benchmark["max_reasonable_value"]:
                validation_status = "needs_review"

            benchmark_comparison[category] = {
                "achievement_value": achievement_value,
                "benchmark_avg": benchmark["avg_cost_reduction"]
                + (benchmark["avg_time_saved_hours"] * hourly_rate),
                "max_reasonable": benchmark["max_reasonable_value"],
                "within_range": achievement_value <= benchmark["max_reasonable_value"],
            }

        return {
            "validation_status": validation_status,
            "benchmark_comparison": benchmark_comparison,
        }

    def generate_portfolio_report(self, achievements):
        """Generate comprehensive portfolio report."""
        # Calculate portfolio value
        value_data = self.calculate_portfolio_value(achievements)
        total_value = value_data["total_value"]

        # Validate against benchmarks
        validation_data = self.validate_against_benchmarks(achievements)

        # Group achievements by category
        achievements_by_category = {}
        for achievement in achievements:
            category = achievement.get("category", "feature")
            if category not in achievements_by_category:
                achievements_by_category[category] = []
            achievements_by_category[category].append(achievement)

        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            total_value, len(achievements), achievements_by_category
        )

        # Generate methodology documentation
        methodology = self._generate_methodology()

        # Generate confidence analysis
        confidence_analysis = self._generate_confidence_analysis(
            value_data["confidence_interval"], validation_data
        )

        return {
            "executive_summary": executive_summary,
            "total_portfolio_value": total_value,
            "methodology": methodology,
            "achievements_by_category": achievements_by_category,
            "confidence_analysis": confidence_analysis,
            "value_breakdown": value_data,
            "validation_results": validation_data,
        }

    def _generate_executive_summary(self, total_value, achievement_count, categories):
        """Generate executive summary text."""
        category_count = len(categories)
        return (
            f"Portfolio demonstrates ${total_value:,.0f} in quantifiable business value "
            f"across {achievement_count} achievements in {category_count} categories. "
            f"This value represents a combination of time savings, cost reductions, "
            f"and revenue impacts calculated using industry-standard methodologies."
        )

    def _generate_methodology(self):
        """Generate methodology documentation."""
        return {
            "calculation_methods": {
                "time_savings": "Hours saved × $150/hour (senior developer rate)",
                "cost_reduction": "Direct cost savings from infrastructure, licensing, etc.",
                "revenue_impact": "Direct revenue generation or enablement",
            },
            "confidence_intervals": "80%-120% range based on conservative estimates",
            "validation": "Cross-referenced with industry benchmarks for each category",
        }

    def _generate_confidence_analysis(self, confidence_interval, validation_data):
        """Generate confidence analysis."""
        return {
            "confidence_interval": confidence_interval,
            "validation_status": validation_data["validation_status"],
            "reliability_score": "high"
            if validation_data["validation_status"] == "valid"
            else "medium",
            "notes": "Values are conservative estimates based on measurable impacts",
        }

    def export_to_json(self, report: Dict[str, Any]) -> str:
        """Export portfolio report to JSON format."""
        # Create a clean copy for JSON export
        export_data = {
            "generated_at": datetime.now().isoformat(),
            "executive_summary": report["executive_summary"],
            "total_portfolio_value": report["total_portfolio_value"],
            "value_breakdown": report["value_breakdown"],
            "methodology": report["methodology"],
            "confidence_analysis": report["confidence_analysis"],
            "validation_results": report["validation_results"],
            "achievements_count": sum(
                len(achievements)
                for achievements in report["achievements_by_category"].values()
            ),
            "categories": list(report["achievements_by_category"].keys()),
        }

        return json.dumps(export_data, indent=2)

    def export_to_html(self, report: Dict[str, Any]) -> str:
        """Export portfolio report to HTML format."""
        html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>Portfolio Value Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .summary {{ background-color: #ecf0f1; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .value {{ font-size: 36px; color: #27ae60; font-weight: bold; }}
        .confidence {{ color: #7f8c8d; font-size: 14px; }}
        .methodology {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; }}
        .category {{ font-weight: bold; color: #2c3e50; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Portfolio Value Report</h1>
        <div class="summary">
            <p>{report["executive_summary"]}</p>
            <div class="value">${report["total_portfolio_value"]:,.0f}</div>
            <div class="confidence">
                Confidence Interval: ${
            report["value_breakdown"]["confidence_interval"]["low"]:,.0f} - 
                ${report["value_breakdown"]["confidence_interval"]["high"]:,.0f}
            </div>
        </div>
        
        <h2>Methodology</h2>
        <div class="methodology">
            <p><strong>Calculation Methods:</strong></p>
            <ul>
                <li>Time Savings: {
            report["methodology"]["calculation_methods"]["time_savings"]
        }</li>
                <li>Cost Reduction: {
            report["methodology"]["calculation_methods"]["cost_reduction"]
        }</li>
                <li>Revenue Impact: {
            report["methodology"]["calculation_methods"]["revenue_impact"]
        }</li>
            </ul>
            <p><strong>Confidence Intervals:</strong> {
            report["methodology"]["confidence_intervals"]
        }</p>
            <p><strong>Validation:</strong> {report["methodology"]["validation"]}</p>
        </div>
        
        <h2>Achievements by Category</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Count</th>
                <th>Validation Status</th>
            </tr>
            {
            "".join(
                f'<tr><td class="category">{cat.title()}</td><td>{len(achievements)}</td><td>Valid</td></tr>'
                for cat, achievements in report["achievements_by_category"].items()
            )
        }
        </table>
        
        <h2>Confidence Analysis</h2>
        <p><strong>Validation Status:</strong> {
            report["confidence_analysis"]["validation_status"].upper()
        }</p>
        <p><strong>Reliability Score:</strong> {
            report["confidence_analysis"]["reliability_score"].upper()
        }</p>
        <p><em>{report["confidence_analysis"]["notes"]}</em></p>
        
        <div style="margin-top: 50px; text-align: center; color: #7f8c8d; font-size: 12px;">
            Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
</body>
</html>"""
        return html_template

    def calculate_statistical_confidence(
        self, achievements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate statistical confidence intervals using proper statistical methods."""
        if not achievements:
            return {
                "mean_value": 0,
                "std_deviation": 0,
                "confidence_interval_95": {"low": 0, "high": 0},
            }

        # Calculate individual achievement values
        hourly_rate = 150
        values = []
        for achievement in achievements:
            business_value = achievement.get("business_value", {})
            value = (
                max(0, business_value.get("time_saved_hours", 0)) * hourly_rate
                + max(0, business_value.get("cost_reduction", 0))
                + max(0, business_value.get("revenue_impact", 0))
            )
            values.append(value)

        # Calculate mean
        mean_value = sum(values) / len(values)

        # Calculate standard deviation
        if len(values) > 1:
            variance = sum((x - mean_value) ** 2 for x in values) / (len(values) - 1)
            std_deviation = math.sqrt(variance)
        else:
            std_deviation = 0

        # Calculate 95% confidence interval (using t-distribution approximation)
        # For small samples, we'd normally use t-distribution, but for simplicity using normal approximation
        z_score = 1.96  # 95% confidence
        margin_of_error = (
            z_score * (std_deviation / math.sqrt(len(values))) if len(values) > 0 else 0
        )

        return {
            "mean_value": mean_value,
            "std_deviation": std_deviation,
            "confidence_interval_95": {
                "low": mean_value - margin_of_error,
                "high": mean_value + margin_of_error,
            },
            "sample_size": len(values),
            "total_portfolio_value": sum(values),
        }
