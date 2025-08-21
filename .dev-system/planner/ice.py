"""
M5: ICE Scoring System (Impact, Confidence, Effort)
Intelligent task prioritization for maximum productivity
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

class TaskCategory(Enum):
    """Task categories for context-aware scoring"""
    URGENT_BUG = "urgent_bug"
    FEATURE_DEVELOPMENT = "feature_development"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    QUALITY_IMPROVEMENT = "quality_improvement"
    TECHNICAL_DEBT = "technical_debt"
    LEARNING_DEVELOPMENT = "learning_development"
    SYSTEM_MAINTENANCE = "system_maintenance"

@dataclass
class ICEWeights:
    """Configurable weights for ICE calculation"""
    impact: float = 0.5
    confidence: float = 0.3
    effort: float = 0.2  # Note: effort is inverse (lower = better)

class ICEScorer:
    """Intelligent ICE scoring with context awareness"""
    
    def __init__(self, weights: ICEWeights = None):
        self.weights = weights or ICEWeights()
        
        # Category-specific scoring guidelines
        self.category_guidelines = {
            TaskCategory.URGENT_BUG: {
                'impact_multiplier': 1.2,    # Bugs have higher impact
                'confidence_boost': 1.0,     # Usually clear what needs fixing
                'effort_penalty': 0.8        # Often quicker to fix than estimate
            },
            TaskCategory.FEATURE_DEVELOPMENT: {
                'impact_multiplier': 1.0,    # Standard impact
                'confidence_boost': 0.9,     # Some uncertainty in features
                'effort_penalty': 1.2        # Features often take longer
            },
            TaskCategory.PERFORMANCE_OPTIMIZATION: {
                'impact_multiplier': 1.1,    # Good ROI
                'confidence_boost': 0.8,     # Performance work can be unpredictable
                'effort_penalty': 1.1        # Optimization takes time
            },
            TaskCategory.QUALITY_IMPROVEMENT: {
                'impact_multiplier': 0.8,    # Lower immediate impact
                'confidence_boost': 1.1,     # Usually straightforward
                'effort_penalty': 0.9        # Often quick wins
            },
            TaskCategory.TECHNICAL_DEBT: {
                'impact_multiplier': 0.7,    # Future impact, not immediate
                'confidence_boost': 0.9,     # Usually clear what's needed
                'effort_penalty': 1.3        # Can be time-consuming
            }
        }
    
    def score_task(self, 
                   impact: float, 
                   confidence: float, 
                   effort: float,
                   category: TaskCategory = None,
                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calculate ICE score with intelligent adjustments
        
        Args:
            impact: Impact score 1-10 (higher = more impactful)
            confidence: Confidence score 1-10 (higher = more certain)
            effort: Effort score 1-10 (higher = more effort required)
            category: Task category for context-aware scoring
            context: Additional context for scoring adjustments
            
        Returns:
            Dict with score, adjusted values, and reasoning
        """
        
        # Apply category-specific adjustments
        adjusted_impact = impact
        adjusted_confidence = confidence
        adjusted_effort = effort
        adjustments = []
        
        if category and category in self.category_guidelines:
            guidelines = self.category_guidelines[category]
            
            adjusted_impact *= guidelines['impact_multiplier']
            adjusted_confidence *= guidelines['confidence_boost']
            adjusted_effort *= guidelines['effort_penalty']
            
            adjustments.append(f"Category '{category.value}' adjustments applied")
        
        # Apply context-based adjustments
        if context:
            # Urgency boost
            if context.get('urgent', False):
                adjusted_impact *= 1.3
                adjustments.append("Urgency boost applied")
            
            # Dependency consideration
            if context.get('blocks_others', False):
                adjusted_impact *= 1.2
                adjustments.append("Blocking task boost applied")
            
            # Learning opportunity
            if context.get('learning_opportunity', False):
                adjusted_impact *= 1.1
                adjustments.append("Learning opportunity boost applied")
            
            # Technical risk
            risk_level = context.get('technical_risk', 'medium')
            if risk_level == 'high':
                adjusted_confidence *= 0.8
                adjusted_effort *= 1.2
                adjustments.append("High technical risk penalty applied")
            elif risk_level == 'low':
                adjusted_confidence *= 1.1
                adjustments.append("Low technical risk boost applied")
        
        # Ensure values stay within bounds
        adjusted_impact = max(1.0, min(10.0, adjusted_impact))
        adjusted_confidence = max(1.0, min(10.0, adjusted_confidence))
        adjusted_effort = max(1.0, min(10.0, adjusted_effort))
        
        # Calculate ICE score
        # Formula: (Impact × Impact_Weight × Confidence × Confidence_Weight) / (Effort × Effort_Weight)
        ice_score = (
            (adjusted_impact * self.weights.impact) * 
            (adjusted_confidence * self.weights.confidence)
        ) / (adjusted_effort * self.weights.effort)
        
        return {
            'ice_score': round(ice_score, 2),
            'original_scores': {
                'impact': impact,
                'confidence': confidence,
                'effort': effort
            },
            'adjusted_scores': {
                'impact': round(adjusted_impact, 2),
                'confidence': round(adjusted_confidence, 2),
                'effort': round(adjusted_effort, 2)
            },
            'weights_used': {
                'impact': self.weights.impact,
                'confidence': self.weights.confidence,
                'effort': self.weights.effort
            },
            'adjustments': adjustments,
            'category': category.value if category else None,
            'priority_level': self._get_priority_level(ice_score)
        }
    
    def _get_priority_level(self, ice_score: float) -> str:
        """Convert ICE score to human-readable priority level"""
        if ice_score >= 8.0:
            return "CRITICAL"
        elif ice_score >= 6.0:
            return "HIGH"
        elif ice_score >= 4.0:
            return "MEDIUM"
        elif ice_score >= 2.0:
            return "LOW"
        else:
            return "MINIMAL"
    
    def batch_score_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score multiple tasks and return sorted by ICE score"""
        scored_tasks = []
        
        for task in tasks:
            score_result = self.score_task(
                impact=task['impact'],
                confidence=task['confidence'], 
                effort=task['effort'],
                category=TaskCategory(task.get('category', 'system_maintenance')),
                context=task.get('context', {})
            )
            
            # Merge original task with scoring results
            scored_task = {**task, **score_result}
            scored_tasks.append(scored_task)
        
        # Sort by ICE score (highest first)
        scored_tasks.sort(key=lambda t: t['ice_score'], reverse=True)
        
        return scored_tasks
    
    def suggest_optimal_sequence(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Suggest optimal task execution sequence"""
        scored_tasks = self.batch_score_tasks(tasks)
        
        suggestions = []
        
        # Group by priority level
        critical_tasks = [t for t in scored_tasks if t['priority_level'] == 'CRITICAL']
        high_tasks = [t for t in scored_tasks if t['priority_level'] == 'HIGH']
        medium_tasks = [t for t in scored_tasks if t['priority_level'] == 'MEDIUM']
        
        if critical_tasks:
            suggestions.append("🚨 Start with CRITICAL priorities immediately")
            suggestions.extend([f"  • {t['title']}" for t in critical_tasks])
        
        if high_tasks:
            suggestions.append("🎯 Then tackle HIGH priority items")
            suggestions.extend([f"  • {t['title']}" for t in high_tasks[:3]])
        
        if medium_tasks and len(critical_tasks + high_tasks) < 3:
            suggestions.append("📋 Fill remaining time with MEDIUM priorities")
            suggestions.extend([f"  • {t['title']}" for t in medium_tasks[:2]])
        
        return suggestions

# Example usage and testing
def demo_ice_scoring():
    """Demonstrate ICE scoring with realistic examples"""
    scorer = ICEScorer()
    
    example_tasks = [
        {
            'title': 'Fix critical performance bug',
            'impact': 9.0,
            'confidence': 8.0,
            'effort': 3.0,
            'category': 'urgent_bug',
            'context': {'urgent': True, 'blocks_others': True}
        },
        {
            'title': 'Implement new dashboard feature',
            'impact': 7.0,
            'confidence': 6.0,
            'effort': 8.0,
            'category': 'feature_development',
            'context': {'learning_opportunity': True}
        },
        {
            'title': 'Refactor legacy code module',
            'impact': 5.0,
            'confidence': 7.0,
            'effort': 6.0,
            'category': 'technical_debt',
            'context': {'technical_risk': 'medium'}
        }
    ]
    
    print("🧮 ICE Scoring Demo")
    print("=" * 50)
    
    scored_tasks = scorer.batch_score_tasks(example_tasks)
    
    for task in scored_tasks:
        print(f"\n📋 {task['title']}")
        print(f"   ICE Score: {task['ice_score']} ({task['priority_level']})")
        print(f"   Original: I={task['original_scores']['impact']}, C={task['original_scores']['confidence']}, E={task['original_scores']['effort']}")
        print(f"   Adjusted: I={task['adjusted_scores']['impact']}, C={task['adjusted_scores']['confidence']}, E={task['adjusted_scores']['effort']}")
        if task['adjustments']:
            print(f"   Adjustments: {', '.join(task['adjustments'])}")
    
    print(f"\n🎯 Optimal Sequence:")
    sequence = scorer.suggest_optimal_sequence(example_tasks)
    for suggestion in sequence:
        print(f"   {suggestion}")

if __name__ == "__main__":
    demo_ice_scoring()