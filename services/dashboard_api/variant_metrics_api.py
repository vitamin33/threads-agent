"""
VariantMetricsAPI class for fetching comprehensive variant performance metrics.
Minimal implementation following TDD principles.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session


class VariantMetricsAPI:
    """API for fetching comprehensive variant performance metrics."""
    
    def __init__(
        self, 
        db_session: Optional[Session] = None,
        early_kill_monitor: Optional[Any] = None,
        pattern_fatigue_detector: Optional[Any] = None
    ):
        """Initialize VariantMetricsAPI with dependencies."""
        self.db_session = db_session
        self.early_kill_monitor = early_kill_monitor
        self.pattern_fatigue_detector = pattern_fatigue_detector
    
    def get_comprehensive_metrics(self) -> List[Dict[str, Any]]:
        """
        Get comprehensive metrics for all variants.
        
        Returns:
            List of variant metrics including performance data, early kill status,
            and pattern fatigue warnings.
        """
        if not self.db_session:
            return []
        
        # Import here to avoid circular imports
        from services.orchestrator.db.models import VariantPerformance
        
        # Query all variants from database
        variants = self.db_session.query(VariantPerformance).all()
        
        # Convert to expected format
        result = []
        for variant in variants:
            variant_data = {
                "variant_id": variant.variant_id,
                "impressions": variant.impressions,
                "successes": variant.successes,
                "engagement_rate": variant.success_rate,
            }
            
            # Add early kill status if monitor is available
            if self.early_kill_monitor:
                is_monitored = variant.variant_id in getattr(self.early_kill_monitor, 'active_sessions', {})
                variant_data["early_kill_status"] = "monitoring" if is_monitored else "not_monitored"
            else:
                variant_data["early_kill_status"] = "not_monitored"
            
            # Add pattern fatigue information if detector is available
            if self.pattern_fatigue_detector and hasattr(variant, 'dimensions') and variant.dimensions:
                pattern = variant.dimensions.get('pattern', '')
                if pattern:
                    # For this dashboard, we'll use a placeholder persona_id
                    # In a real implementation, this would come from the variant or context
                    persona_id = "dashboard_analysis"
                    
                    is_fatigued = self.pattern_fatigue_detector.is_pattern_fatigued(pattern, persona_id)
                    freshness_score = self.pattern_fatigue_detector.get_freshness_score(pattern, persona_id)
                    
                    variant_data["pattern_fatigue_warning"] = is_fatigued
                    variant_data["freshness_score"] = freshness_score
                else:
                    variant_data["pattern_fatigue_warning"] = False
                    variant_data["freshness_score"] = 1.0
            else:
                variant_data["pattern_fatigue_warning"] = False
                variant_data["freshness_score"] = 1.0
            
            result.append(variant_data)
        
        return result