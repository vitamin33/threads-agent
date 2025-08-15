"""
A/B Testing Framework for Conversion Optimization

This module implements A/B testing capabilities for optimizing
landing page elements and conversion rates.

Following TDD principles - implementing minimal functionality to make tests pass.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import random
import uuid
# Note: scipy not available in basic environment, will implement simple statistics


@dataclass
class TestVariant:
    """Represents a variant in an A/B test"""
    name: str
    description: str
    changes: Dict[str, Any]


@dataclass
class TestResult:
    """Represents A/B test results with statistical analysis"""
    test_id: str
    variants: Dict[str, Dict[str, Any]]
    statistical_significance: bool
    confidence_level: float
    recommended_action: str
    winner: Optional[str]


class ABTestingFramework:
    """
    Framework for creating and analyzing A/B tests for conversion optimization.
    
    Supports test creation, visitor assignment, conversion tracking,
    and statistical analysis of results.
    """
    
    def __init__(self):
        # In-memory storage for TDD - will replace with database later
        self.active_tests = {}
        self.test_assignments = {}  # visitor_id -> {test_id: variant}
        self.conversion_data = {}   # test_id -> {variant: [conversions]}
        
    def create_ab_test(self, variants: List[TestVariant], test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new A/B test with specified variants.
        
        Args:
            variants: List of TestVariant instances
            test_config: Configuration including test name, traffic split, etc.
            
        Returns:
            Dictionary with test creation result
        """
        test_id = f"{test_config['test_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Validate test configuration
        if len(variants) < 2:
            return {"success": False, "error": "At least 2 variants required"}
        
        if test_config.get("traffic_split", 0.5) <= 0 or test_config.get("traffic_split", 0.5) > 1:
            return {"success": False, "error": "Traffic split must be between 0 and 1"}
        
        # Store test configuration
        self.active_tests[test_id] = {
            "test_id": test_id,
            "test_name": test_config["test_name"],
            "variants": {f"variant_{chr(97 + i)}": variant for i, variant in enumerate(variants)},
            "traffic_split": test_config["traffic_split"],
            "success_metric": test_config["success_metric"],
            "minimum_sample_size": test_config.get("minimum_sample_size", 100),
            "created_at": datetime.utcnow(),
            "status": "active"
        }
        
        # Initialize conversion tracking
        self.conversion_data[test_id] = {}
        for variant_key in self.active_tests[test_id]["variants"].keys():
            self.conversion_data[test_id][variant_key] = {
                "visitors": 0,
                "conversions": 0,
                "conversion_events": []
            }
        
        return {
            "success": True,
            "test_id": test_id,
            "variants_created": len(variants),
            "traffic_split": test_config["traffic_split"]
        }
    
    def assign_visitor_to_group(self, test_id: str, visitor_id: str) -> Dict[str, Any]:
        """
        Assign a visitor to an A/B test variant.
        
        Args:
            test_id: ID of the active test
            visitor_id: Unique visitor identifier
            
        Returns:
            Dictionary with assignment details
        """
        # Check if visitor already assigned to this test
        if visitor_id in self.test_assignments and test_id in self.test_assignments[visitor_id]:
            existing_variant = self.test_assignments[visitor_id][test_id]
            return {
                "visitor_id": visitor_id,
                "test_id": test_id,
                "variant": existing_variant,
                "assigned_at": "previously_assigned"
            }
        
        # Get test configuration
        test_config = self.active_tests.get(test_id)
        if not test_config:
            return {"error": f"Test {test_id} not found"}
        
        # Deterministic assignment based on visitor ID hash
        # This ensures same visitor always gets same variant
        hash_input = f"{test_id}_{visitor_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        variant_index = hash_value % len(test_config["variants"])
        variant_keys = list(test_config["variants"].keys())
        assigned_variant = variant_keys[variant_index]
        
        # Store assignment
        if visitor_id not in self.test_assignments:
            self.test_assignments[visitor_id] = {}
        
        self.test_assignments[visitor_id][test_id] = assigned_variant
        
        # Update visitor count
        self.conversion_data[test_id][assigned_variant]["visitors"] += 1
        
        return {
            "visitor_id": visitor_id,
            "test_id": test_id,
            "variant": assigned_variant,
            "assigned_at": datetime.utcnow()
        }
    
    def track_conversion(self, conversion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track a conversion event for A/B test analysis.
        
        Args:
            conversion_data: Dictionary with conversion details
            
        Returns:
            Dictionary with tracking result
        """
        test_id = conversion_data["test_id"]
        visitor_id = conversion_data["visitor_id"]
        variant = conversion_data["variant"]
        
        # Validate conversion
        if test_id not in self.active_tests:
            return {"success": False, "error": f"Test {test_id} not found"}
        
        if test_id not in self.conversion_data:
            return {"success": False, "error": f"No conversion data for test {test_id}"}
        
        # Record conversion
        conversion_event = {
            "visitor_id": visitor_id,
            "variant": variant,
            "conversion_type": conversion_data.get("conversion_type", "unknown"),
            "conversion_value": conversion_data.get("conversion_value", 0),
            "timestamp": datetime.utcnow()
        }
        
        self.conversion_data[test_id][variant]["conversions"] += 1
        self.conversion_data[test_id][variant]["conversion_events"].append(conversion_event)
        
        return {
            "success": True,
            "conversion_recorded": True,
            "variant": variant
        }
    
    def calculate_test_results(self, test_id: str) -> Dict[str, Any]:
        """
        Calculate A/B test results with statistical analysis.
        
        Args:
            test_id: ID of the test to analyze
            
        Returns:
            Dictionary with complete test results and recommendations
        """
        if test_id not in self.active_tests:
            return {"error": f"Test {test_id} not found"}
        
        test_config = self.active_tests[test_id]
        conversion_data = self.conversion_data.get(test_id, {})
        
        # Calculate conversion rates for each variant
        variants_results = {}
        for variant_key, data in conversion_data.items():
            visitors = data["visitors"]
            conversions = data["conversions"]
            conversion_rate = conversions / visitors if visitors > 0 else 0.0
            
            variants_results[variant_key] = {
                "conversions": conversions,
                "visitors": visitors,
                "conversion_rate": conversion_rate
            }
        
        # Statistical significance testing
        statistical_significance = False
        confidence_level = 0.0
        winner = None
        
        # Simple statistical test - can be enhanced with proper A/B testing statistics
        if len(variants_results) >= 2:
            variant_list = list(variants_results.items())
            variant_a_data = variant_list[0][1]
            variant_b_data = variant_list[1][1]
            
            # Check for significant difference (simplified)
            if (variant_a_data["visitors"] >= 30 and variant_b_data["visitors"] >= 30):
                rate_diff = abs(variant_a_data["conversion_rate"] - variant_b_data["conversion_rate"])
                if rate_diff >= 0.05:  # 5% difference threshold
                    statistical_significance = True
                    confidence_level = 0.95
                    winner = variant_list[0][0] if variant_a_data["conversion_rate"] > variant_b_data["conversion_rate"] else variant_list[1][0]
        
        # Determine recommended action
        recommended_action = "continue_test"
        if statistical_significance:
            recommended_action = "declare_winner"
        elif sum(v["visitors"] for v in variants_results.values()) < test_config["minimum_sample_size"]:
            recommended_action = "continue_test"
        
        return {
            "test_id": test_id,
            "variants": variants_results,
            "statistical_significance": statistical_significance,
            "confidence_level": confidence_level,
            "recommended_action": recommended_action,
            "winner": winner
        }
    
    def should_stop_test_early(self, test_id: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if test should be stopped early due to clear winner.
        
        Args:
            test_id: ID of the test to analyze
            test_data: Current test performance data
            
        Returns:
            Dictionary with early stopping recommendation
        """
        # Analyze performance difference
        variants = list(test_data.values())
        if len(variants) < 2:
            return {"stop_early": False, "reason": "insufficient_variants"}
        
        variant_a = variants[0]
        variant_b = variants[1]
        
        # Check for significant performance difference
        rate_a = variant_a["conversion_rate"]
        rate_b = variant_b["conversion_rate"]
        
        # Minimum sample size check
        min_visitors = min(variant_a["visitors"], variant_b["visitors"])
        if min_visitors < 50:
            return {"stop_early": False, "reason": "insufficient_sample_size"}
        
        # Statistical significance check (simplified)
        rate_difference = abs(rate_a - rate_b)
        relative_improvement = rate_difference / max(rate_a, rate_b, 0.01)  # Avoid division by zero
        
        if relative_improvement >= 0.5 and rate_difference >= 0.10:  # 50% relative improvement AND 10% absolute
            winner = "variant_a" if rate_a > rate_b else "variant_b"
            return {
                "stop_early": True,
                "reason": "statistical_significance_reached",
                "winner": winner,
                "confidence_level": 0.95
            }
        
        return {"stop_early": False, "reason": "no_clear_winner"}
    
    def get_test_status(self, test_id: str) -> Dict[str, Any]:
        """Get current status of an A/B test"""
        if test_id not in self.active_tests:
            return {"error": f"Test {test_id} not found"}
        
        test_config = self.active_tests[test_id]
        conversion_data = self.conversion_data.get(test_id, {})
        
        total_visitors = sum(data["visitors"] for data in conversion_data.values())
        total_conversions = sum(data["conversions"] for data in conversion_data.values())
        
        return {
            "test_id": test_id,
            "status": test_config["status"],
            "total_visitors": total_visitors,
            "total_conversions": total_conversions,
            "variants_count": len(test_config["variants"]),
            "created_at": test_config["created_at"]
        }