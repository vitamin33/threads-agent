"""
Calculation Metadata Utilities for Achievement Collector

Provides calculation transparency by storing formulas, inputs, and versions
for all business value and performance metrics calculations.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import json


class CalculationMetadata:
    """Utility class for managing calculation metadata and transparency."""
    
    CALCULATION_VERSION = "v2.1"
    
    @classmethod
    def create_metric_calculation(
        self,
        metric_name: str,
        value: float,
        formula: str,
        inputs: Dict[str, Any],
        baseline_value: Optional[float] = None,
        confidence_score: float = 1.0,
        data_source: str = "computed"
    ) -> Dict[str, Any]:
        """Create enhanced metric with calculation metadata."""
        return {
            "value": value,
            "formula": formula,
            "inputs": inputs,
            "baseline": baseline_value,
            "improvement_factor": value / baseline_value if baseline_value and baseline_value > 0 else 1.0,
            "calculation_version": self.CALCULATION_VERSION,
            "confidence_score": confidence_score,
            "data_source": data_source,
            "calculated_at": datetime.now().isoformat(),
            "methodology": f"Formula: {formula} | Inputs: {json.dumps(inputs, indent=2)}"
        }
    
    @classmethod
    def enhance_business_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance business metrics with calculation transparency."""
        enhanced = {}
        
        # ROI Calculation
        if "roi_year_one_percent" in metrics:
            roi_value = metrics["roi_year_one_percent"]
            # Try to extract inputs from context
            annual_savings = metrics.get("infrastructure_savings_estimate", 0)
            dev_cost = metrics.get("development_cost_estimate", 150000)
            
            enhanced["roi_calculation"] = self.create_metric_calculation(
                metric_name="roi_year_one_percent",
                value=roi_value,
                formula="(annual_savings / development_cost) * 100",
                inputs={
                    "annual_savings": annual_savings,
                    "development_cost": dev_cost
                },
                confidence_score=0.8,
                data_source="estimated"
            )
        
        # Infrastructure Savings
        if "infrastructure_savings_estimate" in metrics:
            savings_value = metrics["infrastructure_savings_estimate"]
            # Extract performance factor if available
            throughput_improvement = metrics.get("throughput_improvement_percent", 0)
            perf_factor = 1 + (throughput_improvement / 100)
            base_cost = 120000
            
            enhanced["infrastructure_savings"] = self.create_metric_calculation(
                metric_name="infrastructure_savings_estimate",
                value=savings_value,
                formula="base_infrastructure_cost * (performance_factor - 1) / performance_factor",
                inputs={
                    "base_infrastructure_cost": base_cost,
                    "performance_factor": perf_factor,
                    "throughput_improvement_percent": throughput_improvement
                },
                confidence_score=0.7,
                data_source="performance_based"
            )
        
        # User Experience Score
        if "user_experience_score" in metrics:
            ux_score = metrics["user_experience_score"]
            latency = metrics.get("latency_ms", 0)
            
            enhanced["user_experience"] = self.create_metric_calculation(
                metric_name="user_experience_score",
                value=ux_score,
                formula="latency_based_scoring(latency_ms)",
                inputs={
                    "latency_ms": latency,
                    "scoring_rules": {
                        "< 100ms": 10,
                        "< 200ms": 9,
                        "< 500ms": 8,
                        "> 500ms": 7
                    }
                },
                confidence_score=0.9,
                data_source="performance_measurement"
            )
        
        # Time Savings
        if "time_savings_annual" in metrics:
            time_savings = metrics["time_savings_annual"]
            hours_per_week = metrics.get("hours_saved_per_week", 1)
            hourly_rate = 100
            
            enhanced["time_savings"] = self.create_metric_calculation(
                metric_name="time_savings_annual",
                value=time_savings,
                formula="hours_per_week * 50_weeks * hourly_rate",
                inputs={
                    "hours_saved_per_week": hours_per_week,
                    "working_weeks_per_year": 50,
                    "hourly_rate_dollars": hourly_rate
                },
                confidence_score=0.8,
                data_source="productivity_estimate"
            )
        
        return enhanced
    
    @classmethod
    def enhance_performance_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance performance metrics with calculation transparency."""
        enhanced = {}
        
        # Performance Score
        if "performance_score" in metrics:
            perf_score = metrics["performance_score"]
            rps = metrics.get("peak_rps", 0)
            baseline_rps = 100
            
            enhanced["performance_score"] = self.create_metric_calculation(
                metric_name="performance_score",
                value=perf_score,
                formula="actual_rps / baseline_rps",
                inputs={
                    "actual_rps": rps,
                    "baseline_rps": baseline_rps
                },
                baseline_value=1.0,
                confidence_score=0.9,
                data_source="load_testing"
            )
        
        # Quality Score
        if "quality_score" in metrics:
            quality_score = metrics["quality_score"]
            test_coverage = metrics.get("test_coverage", 0)
            
            enhanced["quality_score"] = self.create_metric_calculation(
                metric_name="quality_score",
                value=quality_score,
                formula="test_coverage_percent / 10",
                inputs={
                    "test_coverage_percent": test_coverage
                },
                baseline_value=5.0,
                confidence_score=0.95,
                data_source="test_results"
            )
        
        return enhanced
    
    @classmethod
    def create_calculation_summary(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of all calculations for transparency."""
        return {
            "calculation_version": self.CALCULATION_VERSION,
            "calculated_at": datetime.now().isoformat(),
            "total_metrics": len(metrics),
            "formulas_used": [
                metric.get("formula", "unknown") 
                for metric in metrics.values() 
                if isinstance(metric, dict) and "formula" in metric
            ],
            "confidence_scores": {
                name: metric.get("confidence_score", 0)
                for name, metric in metrics.items()
                if isinstance(metric, dict) and "confidence_score" in metric
            },
            "methodology_notes": [
                "All calculations include transparent formulas and input parameters",
                "Confidence scores reflect reliability of input data and estimation methods",
                "Baseline values provided where applicable for relative comparison",
                "Calculation version tracks methodology changes over time"
            ]
        }