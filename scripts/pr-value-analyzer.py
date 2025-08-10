#!/usr/bin/env python3
"""
Hybrid PR Value Analyzer - Best of Both Worlds

This analyzer combines:
1. Smart adaptive scoring that evaluates PRs based on what they actually deliver
2. Comprehensive business metrics and detailed calculations  
3. Value category detection for intelligent analysis
4. Career-focused outputs (interview points, portfolio summaries)
5. Detailed metric explanations for professional development
"""

import json
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Any
import os
import sys
import math


class HybridPRValueAnalyzer:
    """The ultimate PR analyzer combining smart scoring with comprehensive metrics."""

    def __init__(self, pr_number: str):
        self.pr_number = pr_number
        self.metrics = {
            "pr_number": pr_number,
            "timestamp": datetime.now().isoformat(),
            "value_categories": {},  # What types of value this PR provides
            "business_metrics": {},
            "technical_metrics": {},
            "achievement_tags": [],
            "kpis": {},
            "future_impact": {},
            "active_metrics": {},  # Which metrics are relevant
            "scoring_weights": {},  # Dynamic weights based on PR type
            "pr_type": "unknown",  # Detected PR type for adaptive scoring
        }

    def detect_pr_value_categories(self, pr_data: Dict) -> Dict[str, float]:
        """
        Detect what types of value this PR provides.
        Returns confidence scores for each category.
        """
        title = pr_data.get("title", "").lower()
        body = pr_data.get("body", "").lower()
        files = pr_data.get("files", [])

        categories = {
            "performance": 0.0,
            "business": 0.0,
            "quality": 0.0,
            "documentation": 0.0,
            "infrastructure": 0.0,
            "security": 0.0,
            "user_experience": 0.0,
            "technical_debt": 0.0,
            "innovation": 0.0,
        }

        # Performance indicators
        perf_keywords = [
            "performance", "optimization", "speed", "latency", "rps", "throughput", 
            "cache", "async", "concurrent", "parallel", "scalability"
        ]
        perf_score = sum(1 for kw in perf_keywords if kw in title + body) * 0.15
        if re.search(r"\d+\s*rps|\d+ms\s*latency|throughput|scalability", body, re.IGNORECASE):
            perf_score += 0.6
        if "cleanup" in title.lower():
            perf_score = max(0.3, perf_score)  # Cleanup PRs often have performance impact
        categories["performance"] = min(perf_score, 1.0)

        # Business value indicators
        business_keywords = [
            "roi", "revenue", "cost", "savings", "customer", "user growth", 
            "conversion", "automation", "efficiency", "productivity"
        ]
        business_score = sum(1 for kw in business_keywords if kw in title + body) * 0.2
        if re.search(r"\$\d+|%\s*improvement|%\s*increase|hours saved|cost reduction", body):
            business_score += 0.4
        categories["business"] = min(business_score, 1.0)

        # Quality indicators
        quality_keywords = [
            "test", "coverage", "bug", "fix", "error", "crash", "stability",
            "refactor", "cleanup", "maintainability", "code quality"
        ]
        quality_score = sum(1 for kw in quality_keywords if kw in title + body) * 0.15
        if "cleanup" in title.lower():
            quality_score += 0.7  # Cleanup PRs are primarily quality improvements
        if re.search(r"\d+%\s*coverage|test.*added|bug.*fix", body, re.IGNORECASE):
            quality_score += 0.3
        categories["quality"] = min(quality_score, 1.0)

        # Infrastructure indicators
        infra_keywords = [
            "deployment", "docker", "kubernetes", "ci/cd", "pipeline", "automation",
            "monitoring", "logging", "metrics", "alerts"
        ]
        infra_score = sum(1 for kw in infra_keywords if kw in title + body) * 0.2
        categories["infrastructure"] = min(infra_score, 1.0)

        # Documentation indicators  
        doc_keywords = ["doc", "readme", "guide", "tutorial", "comments", "wiki"]
        doc_score = sum(1 for kw in doc_keywords if kw in title + body) * 0.3
        categories["documentation"] = min(doc_score, 1.0)

        # Security indicators
        security_keywords = [
            "security", "vulnerability", "auth", "encryption", "permissions", "ssl"
        ]
        security_score = sum(1 for kw in security_keywords if kw in title + body) * 0.3
        categories["security"] = min(security_score, 1.0)

        # Innovation indicators
        innovation_keywords = [
            "ai", "ml", "machine learning", "neural", "algorithm", "novel", "innovative",
            "breakthrough", "cutting-edge", "state-of-the-art"
        ]
        innovation_score = sum(1 for kw in innovation_keywords if kw in title + body) * 0.25
        categories["innovation"] = min(innovation_score, 1.0)

        return categories

    def determine_pr_type(self, categories: Dict[str, float]) -> str:
        """Determine the primary PR type based on value categories."""
        if not categories:
            return "unknown"
        
        # Find the category with highest confidence
        primary_category = max(categories.items(), key=lambda x: x[1])
        
        if primary_category[1] < 0.3:
            return "general"
        
        return primary_category[0]

    def get_adaptive_weights(self, pr_type: str) -> Dict[str, float]:
        """Get scoring weights based on PR type."""
        weight_profiles = {
            "performance": {
                "performance_score": 0.5,
                "quality_score": 0.2,
                "business_value_score": 0.2,
                "innovation_score": 0.1,
            },
            "quality": {
                "performance_score": 0.1,
                "quality_score": 0.6,
                "business_value_score": 0.2,
                "innovation_score": 0.1,
            },
            "business": {
                "performance_score": 0.2,
                "quality_score": 0.1,
                "business_value_score": 0.6,
                "innovation_score": 0.1,
            },
            "innovation": {
                "performance_score": 0.2,
                "quality_score": 0.2,
                "business_value_score": 0.2,
                "innovation_score": 0.4,
            },
            "infrastructure": {
                "performance_score": 0.3,
                "quality_score": 0.3,
                "business_value_score": 0.3,
                "innovation_score": 0.1,
            },
            "general": {
                "performance_score": 0.25,
                "quality_score": 0.25,
                "business_value_score": 0.25,
                "innovation_score": 0.25,
            }
        }
        
        return weight_profiles.get(pr_type, weight_profiles["general"])

    def analyze_performance_metrics(self, pr_body: str) -> Dict[str, Any]:
        """Extract comprehensive performance metrics from PR body."""
        metrics = {}

        # RPS (Requests Per Second)
        rps_match = re.search(r"(\d+\.?\d*)\s*RPS", pr_body, re.IGNORECASE)
        if rps_match:
            metrics["peak_rps"] = float(rps_match.group(1))

        # Latency 
        latency_match = re.search(r"<(\d+)ms", pr_body)
        if latency_match:
            metrics["latency_ms"] = int(latency_match.group(1))
        else:
            # Default reasonable latency for analysis
            metrics["latency_ms"] = 200

        # Success Rate
        success_match = re.search(r"(\d+)%\s*success", pr_body, re.IGNORECASE)
        if success_match:
            metrics["success_rate"] = float(success_match.group(1))

        # Error Rate
        error_match = re.search(r"(\d+\.?\d*)%\s*error", pr_body, re.IGNORECASE)
        if error_match:
            metrics["error_rate"] = float(error_match.group(1)) / 100
        else:
            metrics["error_rate"] = 0.01  # Default 1% error rate

        # Test Coverage
        coverage_match = re.search(r"(\d+)%\s*coverage", pr_body, re.IGNORECASE)
        if coverage_match:
            metrics["test_coverage"] = float(coverage_match.group(1))

        # Memory Usage
        memory_match = re.search(r"(\d+\.?\d*)\s*(MB|GB)\s*memory", pr_body, re.IGNORECASE)
        if memory_match:
            memory_val = float(memory_match.group(1))
            unit = memory_match.group(2).upper()
            metrics["memory_usage_mb"] = memory_val if unit == "MB" else memory_val * 1024

        # CPU Usage
        cpu_match = re.search(r"(\d+)%\s*CPU", pr_body, re.IGNORECASE)
        if cpu_match:
            metrics["cpu_usage_percent"] = float(cpu_match.group(1))

        return metrics

    def calculate_comprehensive_business_value(self, performance_metrics: Dict) -> Dict[str, Any]:
        """Calculate comprehensive business value with detailed ROI analysis."""
        business_metrics = {}

        # Base assumptions for calculations
        baseline_rps = 500  # Typical microservice baseline
        developer_hourly_rate = 150  # Industry standard
        server_annual_cost = 12000  # AWS/cloud server cost
        bug_fix_cost = 5000  # Average production bug fix cost

        peak_rps = performance_metrics.get("peak_rps", baseline_rps)
        latency_ms = performance_metrics.get("latency_ms", 200)
        error_rate = performance_metrics.get("error_rate", 0.01)
        test_coverage = performance_metrics.get("test_coverage", 80)

        # Throughput improvement
        if peak_rps > baseline_rps:
            throughput_improvement = ((peak_rps / baseline_rps) - 1) * 100
            business_metrics["throughput_improvement_percent"] = round(throughput_improvement, 1)
            
            # Infrastructure savings from better performance
            servers_reduced = math.floor((peak_rps - baseline_rps) / baseline_rps)
            business_metrics["servers_reduced"] = max(0, servers_reduced)
            business_metrics["infrastructure_savings_estimate"] = servers_reduced * server_annual_cost

        # Developer productivity improvements
        # Estimate based on performance and quality improvements
        productivity_factor = min(2.0, peak_rps / baseline_rps) * (test_coverage / 100)
        productivity_hours_saved = max(0, (productivity_factor - 1) * 40 * 52)  # Hours per year
        business_metrics["productivity_hours_saved"] = round(productivity_hours_saved)
        business_metrics["developer_productivity_savings"] = round(productivity_hours_saved * developer_hourly_rate)

        # Quality improvement savings
        # Higher test coverage and lower error rate prevent bugs
        quality_factor = (test_coverage / 100) * (1 - error_rate) 
        bugs_prevented = max(0, (quality_factor - 0.8) * 20) if quality_factor > 0.8 else 0
        business_metrics["bugs_prevented_annually"] = round(bugs_prevented)
        business_metrics["quality_improvement_savings"] = round(bugs_prevented * bug_fix_cost)

        # Total annual savings
        infrastructure_savings = business_metrics.get("infrastructure_savings_estimate", 0)
        productivity_savings = business_metrics.get("developer_productivity_savings", 0)
        quality_savings = business_metrics.get("quality_improvement_savings", 0)
        
        total_savings = infrastructure_savings + productivity_savings + quality_savings
        business_metrics["total_annual_savings"] = total_savings

        # Risk adjustment based on confidence
        confidence_level = self.determine_confidence_level(performance_metrics)
        confidence_multipliers = {"high": 0.9, "medium": 0.8, "low": 0.7}
        risk_adjusted = total_savings * confidence_multipliers[confidence_level]
        business_metrics["risk_adjusted_savings"] = round(risk_adjusted)
        business_metrics["confidence_level"] = confidence_level

        # Investment calculation (development cost)
        # Estimate based on PR complexity and typical development time
        estimated_dev_hours = self.estimate_development_hours(performance_metrics)
        total_investment = estimated_dev_hours * developer_hourly_rate
        business_metrics["total_investment"] = total_investment

        # ROI calculations
        if total_investment > 0:
            roi_year_one = ((risk_adjusted - total_investment) / total_investment) * 100
            business_metrics["roi_year_one_percent"] = round(roi_year_one, 1)
            
            # Payback period in months
            monthly_savings = risk_adjusted / 12
            if monthly_savings > 0:
                payback_months = total_investment / monthly_savings
                business_metrics["payback_period_months"] = round(payback_months, 1)
            
            # 3-year ROI
            three_year_savings = risk_adjusted * 3
            roi_three_year = ((three_year_savings - total_investment) / total_investment) * 100
            business_metrics["roi_three_year_percent"] = round(roi_three_year, 1)

        # User experience score based on latency
        if latency_ms <= 100:
            ux_score = 10
        elif latency_ms <= 200:
            ux_score = 9
        elif latency_ms <= 300:
            ux_score = 8
        elif latency_ms <= 500:
            ux_score = 7
        elif latency_ms <= 1000:
            ux_score = 5
        else:
            ux_score = 3

        business_metrics["user_experience_score"] = ux_score

        return business_metrics

    def estimate_development_hours(self, performance_metrics: Dict) -> float:
        """Estimate development hours based on performance metrics complexity."""
        base_hours = 20  # Minimum for any PR
        
        # Add complexity based on metrics present
        complexity_factors = {
            "peak_rps": 10 if performance_metrics.get("peak_rps", 0) > 1000 else 5,
            "latency_ms": 8 if performance_metrics.get("latency_ms", 500) < 100 else 4,
            "test_coverage": 15 if performance_metrics.get("test_coverage", 0) > 80 else 5,
            "memory_usage_mb": 6,
            "cpu_usage_percent": 6,
        }
        
        additional_hours = sum(
            complexity_factors.get(metric, 0) 
            for metric in performance_metrics.keys() 
            if performance_metrics[metric] is not None
        )
        
        return base_hours + additional_hours

    def determine_confidence_level(self, performance_metrics: Dict) -> str:
        """Determine confidence level based on available metrics."""
        metric_count = len([v for v in performance_metrics.values() if v is not None])
        
        if metric_count >= 4:
            return "high"
        elif metric_count >= 2:
            return "medium"
        else:
            return "low"

    def calculate_realistic_performance_score(
        self, current_rps: float, latency_ms: float, error_rate: float
    ) -> float:
        """Calculate realistic performance score (0-10) using logarithmic scale."""
        # RPS scoring (logarithmic scale for fairness)
        if current_rps >= 10000:
            rps_score = 10
        elif current_rps >= 5000:
            rps_score = 9
        elif current_rps >= 2000:
            rps_score = 8
        elif current_rps >= 1000:
            rps_score = 7
        elif current_rps >= 500:
            rps_score = 6
        elif current_rps >= 200:
            rps_score = 5
        elif current_rps >= 100:
            rps_score = 4
        elif current_rps >= 50:
            rps_score = 3
        else:
            rps_score = 2

        # Latency scoring (lower is better)
        if latency_ms <= 50:
            latency_score = 10
        elif latency_ms <= 100:
            latency_score = 9
        elif latency_ms <= 200:
            latency_score = 8
        elif latency_ms <= 300:
            latency_score = 7
        elif latency_ms <= 500:
            latency_score = 6
        else:
            latency_score = 5

        # Error rate scoring (lower is better)  
        if error_rate <= 0.001:
            error_score = 10
        elif error_rate <= 0.01:
            error_score = 9
        elif error_rate <= 0.02:
            error_score = 8
        elif error_rate <= 0.05:
            error_score = 7
        else:
            error_score = 6

        # Weighted average
        return round((rps_score * 0.5 + latency_score * 0.3 + error_score * 0.2), 1)

    def calculate_adaptive_scores(
        self,
        categories: Dict[str, float],
        performance: Dict[str, Any], 
        business_value: Dict[str, Any],
        code_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate scores with adaptive approach - PRs succeed by excelling in relevant areas."""
        scores = {}

        # Performance score
        performance_score = self.calculate_realistic_performance_score(
            performance.get("peak_rps", 0),
            performance.get("latency_ms", 500),
            performance.get("error_rate", 0.02),
        )
        scores["performance_score"] = performance_score

        # Quality score
        test_coverage = performance.get("test_coverage", 80)
        quality_score = min(10, test_coverage / 10)  # Convert percentage to 0-10 scale
        scores["quality_score"] = quality_score

        # Business value score  
        roi = business_value.get("roi_year_one_percent", 0)
        business_value_score = min(10, max(0, roi / 30))  # Scale ROI to 0-10
        scores["business_value_score"] = business_value_score

        # Innovation score
        innovation_score = self.calculate_innovation_score("", code_metrics)
        scores["innovation_score"] = innovation_score

        # Calculate overall score using adaptive weights
        pr_type = self.determine_pr_type(categories)
        weights = self.get_adaptive_weights(pr_type)
        
        overall_score = sum(
            scores[score_type] * weight
            for score_type, weight in weights.items()
            if score_type in scores
        )
        scores["overall_score"] = round(overall_score, 1)

        # Store metadata
        scores["pr_type"] = pr_type
        scores["scoring_weights"] = weights

        return scores

    def calculate_innovation_score(self, pr_body: str, code_metrics: Dict) -> float:
        """Calculate innovation score based on novelty and technical advancement."""
        score = 5.0  # Base score
        
        # AI/ML keywords
        ai_keywords = ["ai", "ml", "neural", "model", "algorithm", "learning"]
        if any(kw in pr_body.lower() for kw in ai_keywords):
            score += 2.0
            
        # Architecture patterns
        arch_keywords = ["microservice", "serverless", "distributed", "async", "concurrent"]
        if any(kw in pr_body.lower() for kw in arch_keywords):
            score += 1.5
            
        # Performance innovations
        perf_keywords = ["optimization", "cache", "index", "parallel", "stream"]
        if any(kw in pr_body.lower() for kw in perf_keywords):
            score += 1.0
            
        return min(10.0, score)

    def extract_achievement_tags(self, pr_body: str) -> List[str]:
        """Extract relevant achievement tags from PR content."""
        tags = []
        
        # Performance tags
        if re.search(r"\d+\s*rps", pr_body, re.IGNORECASE):
            tags.append("high-performance")
        if re.search(r"<\d+ms", pr_body):
            tags.append("low-latency")
            
        # Quality tags
        if re.search(r"\d+%\s*coverage", pr_body, re.IGNORECASE):
            tags.append("well-tested")
        if "bug" in pr_body.lower() and "fix" in pr_body.lower():
            tags.append("bug-fix")
            
        # Business tags
        if re.search(r"\$\d+|%\s*improvement", pr_body):
            tags.append("business-value")
        if "automation" in pr_body.lower():
            tags.append("automation")
            
        # Innovation tags
        if any(kw in pr_body.lower() for kw in ["ai", "ml", "neural"]):
            tags.append("ai-innovation")
        if "architecture" in pr_body.lower():
            tags.append("architectural")
            
        return tags

    def analyze_code_changes(self) -> Dict[str, Any]:
        """Analyze code changes for technical metrics."""
        try:
            # Get PR diff information
            result = subprocess.run(
                ["gh", "pr", "diff", self.pr_number],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                return {"error": "Could not fetch PR diff"}
                
            diff_content = result.stdout
            
            # Count changes
            lines_added = len(re.findall(r"^\+[^+]", diff_content, re.MULTILINE))
            lines_removed = len(re.findall(r"^-[^-]", diff_content, re.MULTILINE))
            files_changed = len(re.findall(r"^diff --git", diff_content, re.MULTILINE))
            
            # Analyze complexity
            complexity_indicators = [
                "class ", "def ", "function", "import ", "async ", "await "
            ]
            complexity_score = sum(
                diff_content.lower().count(indicator) for indicator in complexity_indicators
            )
            
            return {
                "lines_added": lines_added,
                "lines_removed": lines_removed, 
                "files_changed": files_changed,
                "complexity_score": complexity_score,
                "net_lines": lines_added - lines_removed,
            }
            
        except Exception as e:
            return {"error": f"Code analysis failed: {str(e)}"}

    def generate_future_impact(self, business_value: Dict, performance: Dict) -> Dict:
        """Generate future impact projections."""
        future_impact = {}
        
        # Revenue impact projection (conservative 3-year estimate)
        annual_savings = business_value.get("risk_adjusted_savings", 0)
        if annual_savings > 0:
            # Assume 10% compound growth in value over 3 years
            three_year_revenue = annual_savings * 3.31  # 1.1^3 ≈ 3.31
            future_impact["revenue_impact_3yr"] = round(three_year_revenue)
            
        # Competitive advantage
        peak_rps = performance.get("peak_rps", 0)
        if peak_rps > 5000:
            future_impact["competitive_advantage"] = "High performance enables new market opportunities"
        elif peak_rps > 1000:
            future_impact["competitive_advantage"] = "Performance improvements support growth"
            
        # Technical debt reduction
        test_coverage = performance.get("test_coverage", 0)
        if test_coverage > 80:
            maintenance_reduction = min(30, (test_coverage - 70) * 2)
            future_impact["maintenance_cost_reduction_percent"] = maintenance_reduction
            
        return future_impact

    def run_analysis(self):
        """Run comprehensive PR analysis with adaptive scoring."""
        try:
            print(f"🔍 Analyzing PR #{self.pr_number}...")
            
            # Get PR data
            result = subprocess.run(
                ["gh", "pr", "view", self.pr_number, "--json", "title,body,files"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                print(f"❌ Error: Could not fetch PR #{self.pr_number}")
                return None
                
            pr_data = json.loads(result.stdout)
            pr_body = pr_data.get("body", "")
            
            # Detect value categories (key innovation)
            categories = self.detect_pr_value_categories(pr_data)
            self.metrics["value_categories"] = categories
            
            # Determine PR type for adaptive scoring
            pr_type = self.determine_pr_type(categories)
            self.metrics["pr_type"] = pr_type
            
            print(f"📊 Detected PR Type: {pr_type}")
            print(f"🎯 Value Categories: {', '.join(k for k,v in categories.items() if v > 0.3)}")
            
            # Extract performance metrics
            performance = self.analyze_performance_metrics(pr_body)
            self.metrics["technical_metrics"]["performance"] = performance
            
            # Calculate comprehensive business value
            business_value = self.calculate_comprehensive_business_value(performance)
            self.metrics["business_metrics"] = business_value
            
            # Analyze code changes
            code_metrics = self.analyze_code_changes()
            self.metrics["technical_metrics"]["code_changes"] = code_metrics
            
            # Calculate adaptive scores
            kpis = self.calculate_adaptive_scores(categories, performance, business_value, code_metrics)
            self.metrics["kpis"] = kpis
            self.metrics["scoring_weights"] = kpis.get("scoring_weights", {})
            
            # Extract achievement tags
            tags = self.extract_achievement_tags(pr_body)
            self.metrics["achievement_tags"] = tags
            
            # Generate future impact
            future_impact = self.generate_future_impact(business_value, performance)
            self.metrics["future_impact"] = future_impact
            
            return self.metrics
            
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            return None

    def save_results(self, output_file: str = None):
        """Save analysis results to file."""
        if not output_file:
            output_file = f"pr_{self.pr_number}_value_analysis.json"
            
        with open(output_file, "w") as f:
            json.dump(self.metrics, f, indent=2)
            
        print(f"✅ Results saved to {output_file}")
        
        # Also save achievement file for tracking
        achievement_file = f".achievements/pr_{self.pr_number}_achievement.json"
        os.makedirs(".achievements", exist_ok=True)
        
        achievement_data = {
            "pr_number": self.pr_number,
            "timestamp": self.metrics["timestamp"],
            "overall_score": self.metrics["kpis"].get("overall_score", 0),
            "business_value": self.metrics["business_metrics"],
            "achievement_tags": self.metrics["achievement_tags"],
            "pr_type": self.metrics["pr_type"],
            "value_categories": self.metrics["value_categories"],
            "metric_explanations": self._generate_metric_explanations_dict(),
        }
        
        with open(achievement_file, "w") as f:
            json.dump(achievement_data, f, indent=2)
            
        print(f"✅ Achievement data saved to {achievement_file}")

    def print_summary(self):
        """Print comprehensive analysis summary."""
        print("\n" + "=" * 80)
        print(f"📊 PR #{self.pr_number} VALUE ANALYSIS SUMMARY")
        print("=" * 80)
        
        # PR Type and Categories
        print(f"\n🎯 PR TYPE: {self.metrics['pr_type'].upper()}")
        categories = self.metrics.get("value_categories", {})
        active_categories = [(k, v) for k, v in categories.items() if v > 0.3]
        if active_categories:
            print("📈 VALUE CATEGORIES:")
            for category, confidence in sorted(active_categories, key=lambda x: x[1], reverse=True):
                print(f"   • {category}: {confidence:.1%} confidence")
        
        # KPIs with adaptive context
        kpis = self.metrics.get("kpis", {})
        weights = self.metrics.get("scoring_weights", {})
        
        print(f"\n🏆 OVERALL SCORE: {kpis.get('overall_score', 0)}/10 {self._get_score_status(kpis.get('overall_score', 0))}")
        
        print("\n📊 SCORE BREAKDOWN (with adaptive weights):")
        score_items = [
            ("Performance", "performance_score"),
            ("Quality", "quality_score"), 
            ("Business Value", "business_value_score"),
            ("Innovation", "innovation_score"),
        ]
        
        for name, key in score_items:
            score = kpis.get(key, 0)
            weight = weights.get(key, 0.25)
            print(f"   • {name}: {score}/10 (weight: {weight:.0%}) {self._get_score_status(score)}")
        
        # Business Metrics
        business = self.metrics.get("business_metrics", {})
        if business:
            print(f"\n💰 BUSINESS VALUE:")
            if "roi_year_one_percent" in business:
                print(f"   • ROI (Year 1): {business['roi_year_one_percent']:.1f}%")
            if "total_annual_savings" in business:
                print(f"   • Annual Savings: ${business['total_annual_savings']:,}")
            if "payback_period_months" in business:
                print(f"   • Payback Period: {business['payback_period_months']} months")
            if "confidence_level" in business:
                print(f"   • Confidence: {business['confidence_level'].upper()}")
        
        # Performance Metrics
        performance = self.metrics.get("technical_metrics", {}).get("performance", {})
        if performance:
            print(f"\n🚀 PERFORMANCE:")
            if "peak_rps" in performance:
                print(f"   • Peak RPS: {performance['peak_rps']:,}")
            if "latency_ms" in performance:
                print(f"   • Latency: {performance['latency_ms']}ms")
            if "test_coverage" in performance:
                print(f"   • Test Coverage: {performance['test_coverage']}%")
        
        # Achievement Tags
        tags = self.metrics.get("achievement_tags", [])
        if tags:
            print(f"\n🏷️  ACHIEVEMENT TAGS: {', '.join(tags)}")
        
        print("\n" + "=" * 80)

    def _get_score_status(self, score: float) -> str:
        """Get status emoji for score."""
        if score >= 8:
            return "🌟"
        elif score >= 6:
            return "✅"
        elif score >= 4:
            return "⚠️"
        else:
            return "❌"

    def _generate_metric_explanations_dict(self) -> Dict[str, Dict[str, Any]]:
        """Generate comprehensive metric explanations."""
        explanations = {
            "business_metrics": {
                "throughput_improvement_percent": {
                    "formula": "((current_rps / baseline_rps) - 1) × 100%",
                    "meaning": "How much faster the system processes requests vs baseline",
                    "baseline": "500 RPS (typical microservice performance)",
                },
                "infrastructure_savings_estimate": {
                    "formula": "servers_reduced × $12k/year + bandwidth_savings",
                    "meaning": "Annual cost reduction from needing fewer servers",
                },
                "developer_productivity_savings": {
                    "formula": "hours_saved × $150/hour",
                    "meaning": "Cost savings from developers working more efficiently",
                },
                "quality_improvement_savings": {
                    "formula": "bugs_prevented × $5k/bug",
                    "meaning": "Cost avoided by catching bugs before production",
                },
                "roi_year_one_percent": {
                    "formula": "((annual_savings - investment) / investment) × 100%",
                    "meaning": "Return on investment in the first year",
                },
                "user_experience_score": {
                    "scale": {
                        "10": "<100ms (Exceptional)",
                        "9": "<200ms (Excellent)", 
                        "7": "<500ms (Good)",
                        "5": ">500ms (Needs improvement)",
                    },
                },
            },
            "adaptive_scoring": {
                "pr_type_detection": {
                    "method": "Analyze title, body, and files to determine primary value category",
                    "categories": ["performance", "quality", "business", "innovation", "infrastructure"]
                },
                "adaptive_weights": {
                    "performance_pr": {"performance": "50%", "quality": "20%", "business": "20%", "innovation": "10%"},
                    "quality_pr": {"quality": "60%", "performance": "10%", "business": "20%", "innovation": "10%"},
                    "business_pr": {"business": "60%", "performance": "20%", "quality": "10%", "innovation": "10%"},
                },
                "fairness_principle": "PRs can succeed by excelling in their relevant areas, not all areas"
            }
        }
        return explanations

    def generate_portfolio_summary(self) -> str:
        """Generate portfolio-ready project summary for career use."""
        business = self.metrics.get("business_metrics", {})
        performance = self.metrics.get("technical_metrics", {}).get("performance", {})
        pr_type = self.metrics.get("pr_type", "general")
        
        # Customize summary based on PR type
        if pr_type == "performance":
            title = "High-Performance System Optimization"
            focus = "performance engineering and scalability"
        elif pr_type == "quality":
            title = "Code Quality and Testing Enhancement" 
            focus = "software quality assurance and maintainability"
        elif pr_type == "business":
            title = "Business Value Delivery Project"
            focus = "ROI-driven development and cost optimization"
        else:
            title = "Full-Stack Technical Implementation"
            focus = "comprehensive system improvements"
            
        roi = business.get("roi_year_one_percent", 0)
        annual_savings = business.get("total_annual_savings", 0)
        peak_rps = performance.get("peak_rps", 0)
        
        summary = f"""**{title}**

Led the development and implementation of a {focus} solution that delivered measurable business impact and technical excellence.

**Key Achievements:**
"""
        
        if peak_rps > 1000:
            summary += f"• Achieved {peak_rps:,} RPS throughput with optimized performance architecture\n"
        if annual_savings > 10000:
            summary += f"• Generated ${annual_savings:,} in projected annual savings through efficiency improvements\n"
        if roi > 100:
            summary += f"• Delivered {roi:.1f}% ROI in first year with strategic technical investments\n"
        
        summary += f"""
**Technical Impact:**
• Implemented {pr_type} improvements using modern engineering practices
• Ensured production reliability with comprehensive testing and monitoring
• Designed scalable solutions following industry best practices

**Business Value:**
• Quantified financial impact with detailed ROI analysis
• Reduced operational costs through performance optimizations  
• Enhanced user experience with improved system responsiveness

This project demonstrates my ability to bridge technical excellence with business value, delivering solutions that are both technically sound and financially beneficial.
"""
        
        return summary

def main():
    if len(sys.argv) != 2:
        print("Usage: python pr-value-analyzer.py <PR_NUMBER>")
        sys.exit(1)
        
    pr_number = sys.argv[1]
    analyzer = HybridPRValueAnalyzer(pr_number)
    
    # Run analysis
    results = analyzer.run_analysis()
    if not results:
        sys.exit(1)
        
    # Save results
    analyzer.save_results()
    
    # Print summary
    analyzer.print_summary()
    
    # Generate portfolio summary
    portfolio_summary = analyzer.generate_portfolio_summary()
    print(f"\n📋 PORTFOLIO SUMMARY:")
    print("-" * 40)
    print(portfolio_summary)

if __name__ == "__main__":
    main()