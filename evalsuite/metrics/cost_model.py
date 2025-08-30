#!/usr/bin/env python3
"""
Cost Model - Local vs Cloud Economic Analysis

Calculates cost per request with sensitivity analysis
for Apple Silicon local deployment vs cloud APIs.
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class CostAnalysis:
    """Cost analysis results."""
    local_cost_per_request: float
    cloud_cost_per_request: float
    savings_percent: float
    annual_savings_1k_requests: float
    sensitivity_range: Tuple[float, float]


class CostModel:
    """Economic analysis for local vs cloud deployment."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize cost model."""
        self.kwh_rate = config["power"]["kwh_rate"]
        self.m4_max_tdp = config["power"]["m4_max_tdp"]  # watts
        self.cloud_price_per_1k = config["cloud_baseline"]["price_per_1k_output_tokens"]
    
    def calculate_local_cost(
        self, 
        inference_time_ms: float, 
        output_tokens: int
    ) -> float:
        """Calculate local inference cost based on M4 Max power consumption."""
        
        # Power cost calculation
        inference_time_hours = inference_time_ms / (1000 * 3600)
        power_cost_per_hour = (self.m4_max_tdp / 1000) * self.kwh_rate
        
        # Cost per request
        local_cost = inference_time_hours * power_cost_per_hour
        
        return local_cost
    
    def calculate_cloud_cost(self, output_tokens: int) -> float:
        """Calculate cloud API cost."""
        return (output_tokens / 1000) * self.cloud_price_per_1k
    
    def analyze_cost_efficiency(
        self,
        model_performance: Dict[str, Any],
        output_lengths: List[int] = [128, 384]
    ) -> Dict[int, CostAnalysis]:
        """Analyze cost efficiency for different output lengths."""
        
        print("💰 Analyzing cost efficiency...")
        
        results = {}
        
        for output_length in output_lengths:
            # Use median latency for cost calculation
            latency_ms = model_performance.get("p50_latency_ms", 1000)
            
            # Calculate costs
            local_cost = self.calculate_local_cost(latency_ms, output_length)
            cloud_cost = self.calculate_cloud_cost(output_length)
            
            # Savings analysis
            savings_percent = ((cloud_cost - local_cost) / cloud_cost) * 100
            annual_savings = (cloud_cost - local_cost) * 365 * 1000  # 1k requests/day
            
            # Sensitivity analysis (±10% on power costs)
            sensitivity_low = self.calculate_local_cost(latency_ms, output_length) * 0.9
            sensitivity_high = self.calculate_local_cost(latency_ms, output_length) * 1.1
            
            results[output_length] = CostAnalysis(
                local_cost_per_request=local_cost,
                cloud_cost_per_request=cloud_cost,
                savings_percent=savings_percent,
                annual_savings_1k_requests=annual_savings,
                sensitivity_range=(
                    ((cloud_cost - sensitivity_high) / cloud_cost) * 100,
                    ((cloud_cost - sensitivity_low) / cloud_cost) * 100
                )
            )
            
            print(f"   📊 {output_length} tokens: {savings_percent:.1f}% savings")
        
        return results
    
    def generate_cost_sensitivity_table(
        self, 
        model_performances: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate cost sensitivity table."""
        
        table_lines = [
            "# Cost Analysis - Local Apple Silicon vs Cloud APIs",
            "",
            "## Cost per Request Sensitivity Analysis",
            "",
            "| Model | Output Length | Local Cost | Cloud Cost | Savings | Sensitivity Range |",
            "|-------|---------------|------------|------------|---------|-------------------|"
        ]
        
        for model_id, performance in model_performances.items():
            cost_analysis = self.analyze_cost_efficiency(performance)
            
            for output_length, analysis in cost_analysis.items():
                local_cost = analysis.local_cost_per_request
                cloud_cost = analysis.cloud_cost_per_request
                savings = analysis.savings_percent
                sens_low, sens_high = analysis.sensitivity_range
                
                table_lines.append(
                    f"| {model_id} | {output_length} | ${local_cost:.6f} | ${cloud_cost:.6f} | "
                    f"{savings:.1f}% | {sens_low:.1f}% - {sens_high:.1f}% |"
                )
        
        # Add hardware amortization note
        table_lines.extend([
            "",
            "## Hardware Amortization Notes",
            "",
            "**Apple Silicon M4 Max Local Deployment:**",
            "- Hardware cost amortization: ~$0.50-1.00 per day over 3-year lifecycle",
            "- Electricity cost: Based on 35W TDP during ML workload",
            "- Additional benefits: Data privacy, no rate limits, offline capability",
            "",
            "**Cloud Baseline:**", 
            f"- Small instruct model pricing: ${self.cloud_price_per_1k:.2f} per 1K output tokens",
            "- Additional costs: API rate limits, data transfer, vendor lock-in",
            "",
            "*Note: Hardware amortization costs are minimal compared to cloud savings at scale.*"
        ])
        
        return "\\n".join(table_lines)


def create_cost_model(config: Dict[str, Any]) -> CostModel:
    """Create cost model from configuration."""
    return CostModel(config)