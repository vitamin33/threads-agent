"""Test Portfolio Value Validation & Metrics Generation - TDD approach."""

from services.achievement_collector.services.portfolio_validator import (
    PortfolioValidator,
)


class TestPortfolioValidator:
    """Test suite for Portfolio Value Validation following TDD principles."""

    def test_portfolio_validator_exists(self):
        """Test that PortfolioValidator class can be instantiated."""
        # This will fail - class doesn't exist yet
        validator = PortfolioValidator()
        assert validator is not None

    def test_calculate_portfolio_value_with_no_achievements(self):
        """Test that portfolio value is 0 with no achievements."""
        validator = PortfolioValidator()
        achievements = []

        result = validator.calculate_portfolio_value(achievements)

        assert result["total_value"] == 0
        assert result["confidence_interval"]["low"] == 0
        assert result["confidence_interval"]["high"] == 0

    def test_calculate_portfolio_value_with_single_achievement(self):
        """Test portfolio value calculation with a single achievement."""
        validator = PortfolioValidator()
        achievements = [
            {
                "pr_number": 123,
                "title": "Implement caching system",
                "business_value": {
                    "time_saved_hours": 100,
                    "cost_reduction": 50000,
                    "revenue_impact": 0,
                },
            }
        ]

        result = validator.calculate_portfolio_value(achievements)

        # 100 hours * $150/hour + $50,000 cost reduction
        expected_value = 100 * 150 + 50000  # $65,000
        assert result["total_value"] == expected_value
        assert (
            result["confidence_interval"]["low"] == expected_value * 0.8
        )  # 80% confidence
        assert (
            result["confidence_interval"]["high"] == expected_value * 1.2
        )  # 120% confidence

    def test_validate_against_benchmarks(self):
        """Test validation against industry benchmarks."""
        validator = PortfolioValidator()

        achievements = [
            {
                "pr_number": 456,
                "title": "Infrastructure optimization",
                "business_value": {
                    "time_saved_hours": 500,
                    "cost_reduction": 100000,
                    "revenue_impact": 0,
                },
                "category": "infrastructure",
            }
        ]

        result = validator.validate_against_benchmarks(achievements)

        assert "validation_status" in result
        assert "benchmark_comparison" in result
        assert result["validation_status"] == "valid"
        assert "infrastructure" in result["benchmark_comparison"]

    def test_generate_portfolio_report_basic(self):
        """Test basic portfolio report generation."""
        validator = PortfolioValidator()

        achievements = [
            {
                "pr_number": 789,
                "title": "API Performance Optimization",
                "description": "Reduced API latency by 50%",
                "business_value": {
                    "time_saved_hours": 200,
                    "cost_reduction": 30000,
                    "revenue_impact": 20000,
                },
                "category": "performance",
                "date": "2024-01-15",
            }
        ]

        report = validator.generate_portfolio_report(achievements)

        assert "executive_summary" in report
        assert "total_portfolio_value" in report
        assert "methodology" in report
        assert "achievements_by_category" in report
        assert "confidence_analysis" in report

    def test_export_to_json(self):
        """Test exporting portfolio report to JSON format."""
        validator = PortfolioValidator()

        achievements = [
            {
                "pr_number": 101,
                "title": "Database optimization",
                "business_value": {
                    "time_saved_hours": 100,
                    "cost_reduction": 20000,
                    "revenue_impact": 0,
                },
            }
        ]

        report = validator.generate_portfolio_report(achievements)
        json_output = validator.export_to_json(report)

        assert isinstance(json_output, str)
        import json

        parsed = json.loads(json_output)
        assert "total_portfolio_value" in parsed
        assert "executive_summary" in parsed

    def test_export_to_html(self):
        """Test exporting portfolio report to HTML format."""
        validator = PortfolioValidator()

        achievements = [
            {
                "pr_number": 102,
                "title": "Security Enhancement",
                "business_value": {
                    "time_saved_hours": 150,
                    "cost_reduction": 40000,
                    "revenue_impact": 0,
                },
                "category": "security",
            }
        ]

        report = validator.generate_portfolio_report(achievements)
        html_output = validator.export_to_html(report)

        assert isinstance(html_output, str)
        assert "<html>" in html_output
        assert "Portfolio Value Report" in html_output
        assert "$62,500" in html_output  # 150 * 150 + 40000

    def test_portfolio_value_in_target_range(self):
        """Test that realistic portfolio achieves target value range ($200K-350K)."""
        validator = PortfolioValidator()

        # Simulate a realistic portfolio of achievements
        achievements = [
            {
                "pr_number": 1,
                "title": "Infrastructure Automation",
                "business_value": {
                    "time_saved_hours": 300,  # $45K
                    "cost_reduction": 80000,  # $80K
                    "revenue_impact": 0,
                },
                "category": "infrastructure",
            },
            {
                "pr_number": 2,
                "title": "Performance Optimization",
                "business_value": {
                    "time_saved_hours": 200,  # $30K
                    "cost_reduction": 50000,  # $50K
                    "revenue_impact": 0,
                },
                "category": "performance",
            },
            {
                "pr_number": 3,
                "title": "Security Implementation",
                "business_value": {
                    "time_saved_hours": 150,  # $22.5K
                    "cost_reduction": 40000,  # $40K
                    "revenue_impact": 0,
                },
                "category": "security",
            },
        ]

        result = validator.calculate_portfolio_value(achievements)

        # Total should be: 45K + 80K + 30K + 50K + 22.5K + 40K = $267.5K
        assert 200000 <= result["total_value"] <= 350000
        assert result["total_value"] == 267500

    def test_statistical_confidence_calculation(self):
        """Test statistical confidence interval calculation with multiple achievements."""
        validator = PortfolioValidator()

        achievements = [
            {
                "pr_number": i,
                "title": f"Achievement {i}",
                "business_value": {
                    "time_saved_hours": 50 + (i * 10),  # Varying values
                    "cost_reduction": 10000 + (i * 5000),
                    "revenue_impact": 0,
                },
                "category": "feature",
            }
            for i in range(5)
        ]

        result = validator.calculate_statistical_confidence(achievements)

        assert "mean_value" in result
        assert "std_deviation" in result
        assert "confidence_interval_95" in result
        assert result["confidence_interval_95"]["low"] < result["mean_value"]
        assert result["confidence_interval_95"]["high"] > result["mean_value"]

    def test_outlier_detection_and_validation(self):
        """Test that outliers are detected and flagged for review."""
        validator = PortfolioValidator()

        achievements = [
            {
                "pr_number": 999,
                "title": "Unrealistic Achievement",
                "business_value": {
                    "time_saved_hours": 10000,  # Unrealistically high
                    "cost_reduction": 5000000,  # $5M - too high
                    "revenue_impact": 0,
                },
                "category": "feature",
            }
        ]

        validation = validator.validate_against_benchmarks(achievements)

        assert validation["validation_status"] == "needs_review"
        assert not validation["benchmark_comparison"]["feature"]["within_range"]

    def test_edge_case_negative_values(self):
        """Test handling of edge cases like negative values."""
        validator = PortfolioValidator()

        achievements = [
            {
                "pr_number": 666,
                "title": "Edge case test",
                "business_value": {
                    "time_saved_hours": -50,  # Should be treated as 0
                    "cost_reduction": -10000,  # Should be treated as 0
                    "revenue_impact": 50000,
                },
            }
        ]

        result = validator.calculate_portfolio_value(achievements)

        # Should only count positive revenue impact
        assert result["total_value"] == 50000

    def test_complete_portfolio_workflow(self):
        """Test complete workflow from achievements to export."""
        validator = PortfolioValidator()

        # Realistic portfolio of achievements
        achievements = [
            {
                "pr_number": 1001,
                "title": "Kubernetes Migration",
                "description": "Migrated monolith to Kubernetes",
                "business_value": {
                    "time_saved_hours": 400,
                    "cost_reduction": 120000,
                    "revenue_impact": 0,
                },
                "category": "infrastructure",
                "date": "2024-01-15",
            },
            {
                "pr_number": 1002,
                "title": "API Performance Optimization",
                "description": "Reduced API latency by 60%",
                "business_value": {
                    "time_saved_hours": 250,
                    "cost_reduction": 60000,
                    "revenue_impact": 30000,
                },
                "category": "performance",
                "date": "2024-02-20",
            },
            {
                "pr_number": 1003,
                "title": "Security Audit Implementation",
                "description": "Implemented comprehensive security measures",
                "business_value": {
                    "time_saved_hours": 180,
                    "cost_reduction": 50000,
                    "revenue_impact": 0,
                },
                "category": "security",
                "date": "2024-03-10",
            },
        ]

        # Calculate portfolio value
        value_result = validator.calculate_portfolio_value(achievements)
        assert 300000 <= value_result["total_value"] <= 400000

        # Validate against benchmarks
        validation_result = validator.validate_against_benchmarks(achievements)
        assert validation_result["validation_status"] == "valid"

        # Generate comprehensive report
        report = validator.generate_portfolio_report(achievements)
        assert report["total_portfolio_value"] == value_result["total_value"]
        assert len(report["achievements_by_category"]) == 3

        # Test all export formats
        json_export = validator.export_to_json(report)
        assert isinstance(json_export, str)
        assert len(json_export) > 100

        html_export = validator.export_to_html(report)
        assert isinstance(html_export, str)
        assert "<html>" in html_export

        # Calculate statistical confidence
        stats = validator.calculate_statistical_confidence(achievements)
        assert stats["sample_size"] == 3
        assert stats["mean_value"] > 0
        assert stats["std_deviation"] >= 0
