"""VariantMetricsAPI for real-time dashboard data."""

from datetime import datetime
from typing import Dict, List, Any

# Note: These would be imported from actual services in production
# from services.performance_monitor.early_kill import EarlyKillMonitor
# from services.pattern_analyzer.pattern_fatigue_detector import PatternFatigueDetector

# Mock classes for standalone testing
class EarlyKillMonitor:
    pass

class PatternFatigueDetector:
    pass


def get_db_connection():
    """Get database connection."""
    # This will be properly implemented with actual DB connection
    pass


def get_redis_connection():
    """Get Redis connection."""
    # This will be properly implemented with actual Redis connection
    pass


class PerformanceMonitor:
    """Performance monitoring stub."""
    pass


class VariantMetricsAPI:
    """API for fetching variant performance metrics for dashboard."""
    
    def __init__(self):
        """Initialize with database and service connections."""
        self.db = get_db_connection()
        self.redis = get_redis_connection()
        self.performance_monitor = PerformanceMonitor()
        self.early_kill_monitor = EarlyKillMonitor()
        self.fatigue_detector = PatternFatigueDetector()
    
    async def get_live_metrics(self, persona_id: str) -> Dict[str, Any]:
        """Get comprehensive variant performance overview."""
        return {
            "summary": await self.get_performance_summary(persona_id),
            "active_variants": await self.get_active_variants(persona_id),
            "performance_leaders": await self.get_top_performers(persona_id),
            "early_kills_today": await self.get_kill_statistics(persona_id),
            "pattern_fatigue_warnings": await self.get_fatigue_warnings(persona_id),
            "optimization_opportunities": await self.get_optimization_suggestions(persona_id),
            "real_time_feed": await self.get_recent_events(persona_id)
        }
    
    async def get_performance_summary(self, persona_id: str) -> Dict[str, Any]:
        """Get high-level performance summary."""
        # Implementation placeholder
        return {"total_variants": 0, "avg_engagement_rate": 0.0}
    
    async def get_active_variants(self, persona_id: str) -> List[Dict[str, Any]]:
        """Get all currently active variants with live performance data."""
        # Handle case where db is not initialized (for testing)
        if self.db is None:
            return []
            
        # Fetch variants from database
        query = """
            SELECT v.id, v.content, v.predicted_er, v.posted_at,
                   m.current_er, m.interaction_count, m.status
            FROM variants v
            LEFT JOIN variant_monitoring m ON v.id = m.variant_id
            WHERE v.persona_id = $1 AND v.status = 'active'
            ORDER BY v.posted_at DESC
            LIMIT 50
        """
        
        variants = await self.db.fetch_all(query, persona_id)
        
        # Enhance with real-time performance data
        enhanced_variants = []
        for variant in variants:
            performance = await self.get_variant_performance(variant['id'])
            enhanced_variants.append({
                **dict(variant),
                "live_metrics": performance,
                "time_since_post": self.calculate_time_since_post(variant['posted_at']),
                "performance_vs_prediction": self.calculate_performance_delta(
                    performance.get('engagement_rate', 0), 
                    variant['predicted_er']
                )
            })
        
        return enhanced_variants
    
    async def get_variant_performance(self, variant_id: str) -> Dict[str, Any]:
        """Get real-time performance metrics for a variant."""
        # This would fetch from monitoring service
        return {
            "engagement_rate": 0.0,
            "views": 0,
            "interactions": 0
        }
    
    async def get_top_performers(self, persona_id: str) -> List[Dict[str, Any]]:
        """Get top performing variants."""
        return []
    
    async def get_kill_statistics(self, persona_id: str) -> Dict[str, Any]:
        """Get early kill statistics for today."""
        # Handle case where db is not initialized (for testing)
        if self.db is None:
            return {"kills_today": 0, "avg_time_to_kill_minutes": 0}
            
        query = """
            SELECT 
                COUNT(*) as total_kills,
                AVG(EXTRACT(EPOCH FROM (killed_at - posted_at)) / 60) as avg_time_to_kill
            FROM variant_kills
            WHERE persona_id = $1 
            AND DATE(killed_at) = CURRENT_DATE
        """
        
        result = await self.db.fetch_one(query, persona_id)
        
        if result:
            return {
                "kills_today": result["total_kills"],
                "avg_time_to_kill_minutes": result["avg_time_to_kill"] or 0
            }
        
        return {"kills_today": 0, "avg_time_to_kill_minutes": 0}
    
    async def get_fatigue_warnings(self, persona_id: str) -> List[Dict[str, Any]]:
        """Get pattern fatigue warnings."""
        return []
    
    async def get_optimization_suggestions(self, persona_id: str) -> List[Dict[str, Any]]:
        """Generate actionable optimization recommendations."""
        suggestions = []
        
        # Analyze recent performance patterns
        recent_variants = await self.get_recent_variants(persona_id, hours=24)
        
        # Pattern performance analysis
        pattern_performance = self.analyze_pattern_performance(recent_variants)
        if pattern_performance.get('underperforming'):
            suggestions.append({
                "type": "pattern_optimization",
                "priority": "high",
                "title": "Avoid Underperforming Patterns",
                "description": f"Patterns {pattern_performance['underperforming']} showing <50% expected ER",
                "action": "Pattern fatigue detector will auto-filter these patterns"
            })
        
        # Early kill analysis
        kill_rate = await self.calculate_early_kill_rate(persona_id, hours=24)
        if kill_rate > 0.3:  # >30% kill rate
            suggestions.append({
                "type": "prediction_calibration",
                "priority": "medium", 
                "title": "High Early Kill Rate",
                "description": f"{kill_rate:.1%} variants killed early - prediction model may need recalibration",
                "action": "Review engagement predictor accuracy"
            })
        
        return suggestions
    
    async def get_recent_events(self, persona_id: str) -> List[Dict[str, Any]]:
        """Get recent events for real-time feed."""
        return []
    
    def calculate_time_since_post(self, posted_at: datetime) -> str:
        """Calculate human-readable time since post."""
        delta = datetime.now() - posted_at
        
        if delta.total_seconds() < 60:
            return f"{int(delta.total_seconds())}s"
        elif delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)}m"
        elif delta.total_seconds() < 86400:
            return f"{int(delta.total_seconds() / 3600)}h"
        else:
            return f"{int(delta.total_seconds() / 86400)}d"
    
    def calculate_performance_delta(self, actual_er: float, predicted_er: float) -> float:
        """Calculate performance delta as percentage difference from prediction."""
        if predicted_er == 0:
            return 0.0
        return (actual_er - predicted_er) / predicted_er
    
    async def get_recent_variants(self, persona_id: str, hours: int) -> List[Dict[str, Any]]:
        """Get variants from the last N hours."""
        return []
    
    def analyze_pattern_performance(self, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze pattern performance from variants."""
        return {"underperforming": []}
    
    async def calculate_early_kill_rate(self, persona_id: str, hours: int) -> float:
        """Calculate early kill rate for given time period."""
        return 0.0