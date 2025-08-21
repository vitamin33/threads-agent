"""
M5: Evening Debrief System
Tracks outcomes and learns from daily development patterns
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

from ops.telemetry import get_daily_metrics

class EveningDebriefGenerator:
    """Generates evening debriefs and learns from outcomes"""
    
    def __init__(self):
        self.context_dir = DEV_SYSTEM_ROOT / "planner" / "context"
        self.context_dir.mkdir(exist_ok=True)
        
    def load_morning_context(self) -> Optional[Dict[str, Any]]:
        """Load morning brief context for correlation"""
        today = datetime.now().strftime("%Y%m%d")
        context_file = self.context_dir / f"brief_{today}.json"
        
        if not context_file.exists():
            return None
        
        try:
            with open(context_file) as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load morning context: {e}")
            return None
    
    def analyze_day_performance(self) -> Dict[str, Any]:
        """Analyze today's development performance"""
        # Get today's telemetry
        telemetry = get_daily_metrics(1)
        
        # Get git activity
        import subprocess
        
        try:
            # Commits today
            result = subprocess.run([
                'git', 'log', '--since=24 hours ago', '--oneline'
            ], capture_output=True, text=True, cwd=DEV_SYSTEM_ROOT.parent)
            
            commits_today = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # Lines changed
            result = subprocess.run([
                'git', 'diff', '--stat', 'HEAD~1'
            ], capture_output=True, text=True, cwd=DEV_SYSTEM_ROOT.parent)
            
            # Parse git diff stats
            lines_added = 0
            lines_deleted = 0
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if 'insertion' in line or 'deletion' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if 'insertion' in part and i > 0:
                                lines_added += int(parts[i-1])
                            elif 'deletion' in part and i > 0:
                                lines_deleted += int(parts[i-1])
            
            return {
                'telemetry': telemetry,
                'git_activity': {
                    'commits': commits_today,
                    'lines_added': lines_added,
                    'lines_deleted': lines_deleted,
                    'net_lines': lines_added - lines_deleted
                }
            }
            
        except Exception as e:
            print(f"⚠️  Git analysis failed: {e}")
            return {
                'telemetry': telemetry,
                'git_activity': {
                    'commits': 0,
                    'lines_added': 0,
                    'lines_deleted': 0,
                    'net_lines': 0
                }
            }
    
    def calculate_productivity_score(self, performance: Dict[str, Any]) -> float:
        """Calculate overall productivity score for the day"""
        telemetry = performance['telemetry']
        git = performance['git_activity']
        
        # Base score components
        success_rate_score = telemetry['success_rate'] * 40  # 40% weight
        performance_score = min(40, 40 * (5000 / max(1, telemetry['p95_latency_ms'])))  # 40% weight  
        activity_score = min(20, git['commits'] * 4)  # 20% weight (5 commits = max)
        
        total_score = success_rate_score + performance_score + activity_score
        
        return round(total_score, 1)
    
    def generate_insights(self, performance: Dict[str, Any], morning_context: Dict[str, Any] = None) -> List[str]:
        """Generate actionable insights from the day's work"""
        insights = []
        telemetry = performance['telemetry']
        git = performance['git_activity']
        
        # Performance insights
        if telemetry['success_rate'] < 0.9:
            insights.append(f"🔍 Low success rate ({telemetry['success_rate']:.1%}) - investigate error patterns")
        elif telemetry['success_rate'] > 0.95:
            insights.append(f"🎉 Excellent success rate ({telemetry['success_rate']:.1%}) - workflow is stable")
        
        # Latency insights
        if telemetry['p95_latency_ms'] > 3000:
            insights.append(f"⚡ High latency ({telemetry['p95_latency_ms']:.0f}ms) - consider optimization")
        elif telemetry['p95_latency_ms'] < 500:
            insights.append(f"🚀 Great performance ({telemetry['p95_latency_ms']:.0f}ms) - system is responsive")
        
        # Cost insights
        if telemetry['total_cost'] > 5.0:
            insights.append(f"💰 High token costs (${telemetry['total_cost']:.2f}) - review usage patterns")
        elif telemetry['total_cost'] < 1.0:
            insights.append(f"💡 Efficient token usage (${telemetry['total_cost']:.2f}) - good cost control")
        
        # Activity insights
        if git['commits'] > 5:
            insights.append(f"🔥 High activity ({git['commits']} commits) - productive day")
        elif git['commits'] == 0:
            insights.append("🤔 No commits today - consider what blocked progress")
        
        # Code quality insights
        if git['net_lines'] > 500:
            insights.append(f"📈 Significant code growth (+{git['net_lines']} lines) - ensure test coverage")
        elif git['net_lines'] < -200:
            insights.append(f"🧹 Code cleanup ({git['net_lines']} lines) - good refactoring work")
        
        # Morning vs actual correlation
        if morning_context:
            priorities_completed = self._analyze_priority_completion(morning_context, performance)
            if priorities_completed > 0.8:
                insights.append("🎯 Excellent priority execution - morning planning worked well")
            elif priorities_completed < 0.4:
                insights.append("📋 Low priority completion - review planning effectiveness")
        
        return insights
    
    def _analyze_priority_completion(self, morning_context: Dict[str, Any], performance: Dict[str, Any]) -> float:
        """Analyze how well morning priorities were executed (simplified)"""
        # Simplified analysis based on activity level
        commits = performance['git_activity']['commits']
        success_rate = performance['telemetry']['success_rate']
        
        # Rough completion estimate
        completion_score = min(1.0, (commits / 3.0) * success_rate)
        
        return completion_score
    
    def generate_tomorrow_suggestions(self, insights: List[str], performance: Dict[str, Any]) -> List[str]:
        """Generate suggestions for tomorrow based on today's patterns"""
        suggestions = []
        telemetry = performance['telemetry']
        
        # Performance-based suggestions
        if telemetry['failed_calls'] > 10:
            suggestions.append("🔧 Start tomorrow by investigating error patterns")
        
        if telemetry['p95_latency_ms'] > 2000:
            suggestions.append("⚡ Prioritize performance optimization early")
        
        # Pattern-based suggestions
        if performance['git_activity']['commits'] > 3:
            suggestions.append("📝 Consider smaller, more frequent commits")
        elif performance['git_activity']['commits'] == 0:
            suggestions.append("🎯 Set clear coding milestone for tomorrow")
        
        # System improvement suggestions
        suggestions.append("📊 Check morning brief for data-driven priorities")
        suggestions.append("🎯 Use ICE scoring for task prioritization")
        
        return suggestions
    
    def generate_evening_debrief(self) -> str:
        """Generate complete evening debrief"""
        now = datetime.now()
        morning_context = self.load_morning_context()
        performance = self.analyze_day_performance()
        
        productivity_score = self.calculate_productivity_score(performance)
        insights = self.generate_insights(performance, morning_context)
        tomorrow_suggestions = self.generate_tomorrow_suggestions(insights, performance)
        
        debrief_lines = [
            f"🌙 Evening Debrief - {now.strftime('%A, %B %d, %Y')}",
            "=" * 60,
            "",
            f"📊 **Productivity Score: {productivity_score}/100**",
            ""
        ]
        
        # Performance summary
        telemetry = performance['telemetry']
        git = performance['git_activity']
        
        debrief_lines.extend([
            "📈 **Today's Metrics:**",
            f"  • Commits: {git['commits']}",
            f"  • Lines changed: +{git['lines_added']} -{git['lines_deleted']} (net: {git['net_lines']:+d})",
            f"  • Success rate: {telemetry['success_rate']:.1%}",
            f"  • Avg latency: {telemetry['p95_latency_ms']:.0f}ms",
            f"  • Cost: ${telemetry['total_cost']:.2f}",
            ""
        ])
        
        # Morning priorities vs actual (if available)
        if morning_context:
            debrief_lines.extend([
                "🎯 **Morning Priorities Review:**",
                "  Today's planned priorities:"
            ])
            
            for i, priority in enumerate(morning_context.get('priorities', [])[:3], 1):
                debrief_lines.append(f"  {i}. {priority['title']} (ICE: {priority['ice_score']})")
            
            completion_rate = self._analyze_priority_completion(morning_context, performance)
            debrief_lines.extend([
                f"  📊 Estimated completion: {completion_rate:.1%}",
                ""
            ])
        
        # Key insights
        if insights:
            debrief_lines.extend([
                "💡 **Key Insights:**",
                *[f"  • {insight}" for insight in insights],
                ""
            ])
        
        # Tomorrow's suggestions
        debrief_lines.extend([
            "🌅 **Tomorrow's Focus:**",
            *[f"  • {suggestion}" for suggestion in tomorrow_suggestions],
            "",
            "📋 **Quick Start Tomorrow:**",
            "  1. `just brief` - Get data-driven morning priorities",
            "  2. `just metrics-today` - Check overnight system health",  
            "  3. Focus on top ICE-scored priority first",
            "",
            f"Generated at {now.strftime('%H:%M')} • Next brief available at 6:00 AM"
        ])
        
        # Save debrief for learning
        self._save_debrief_data(performance, productivity_score, insights)
        
        return "\n".join(debrief_lines)
    
    def _save_debrief_data(self, performance: Dict[str, Any], score: float, insights: List[str]):
        """Save debrief data for learning and trend analysis"""
        today = datetime.now().strftime("%Y%m%d")
        debrief_file = self.context_dir / f"debrief_{today}.json"
        
        debrief_data = {
            'date': today,
            'timestamp': datetime.now().isoformat(),
            'productivity_score': score,
            'performance': performance,
            'insights_count': len(insights),
            'insights': insights
        }
        
        with open(debrief_file, 'w') as f:
            json.dump(debrief_data, f, indent=2)

def generate_evening_debrief() -> str:
    """Main entry point for evening debrief generation"""
    generator = EveningDebriefGenerator()
    return generator.generate_evening_debrief()

def main():
    """CLI entry point"""
    debrief = generate_evening_debrief()
    print(debrief)

if __name__ == "__main__":
    main()