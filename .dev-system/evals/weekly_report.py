"""
M7: Weekly Quality Report System
Comprehensive quality analysis and trends across all agents
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

class WeeklyQualityReporter:
    """Generates comprehensive weekly quality reports"""
    
    def __init__(self):
        self.reports_dir = DEV_SYSTEM_ROOT / "evals" / "reports"
        
    def get_weekly_data(self, days_back: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """Get evaluation data from the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        agent_data = defaultdict(list)
        
        if not self.reports_dir.exists():
            return {}
        
        # Collect single agent results
        for report_file in self.reports_dir.glob("eval_*.json"):
            try:
                # Extract timestamp from filename
                parts = report_file.stem.split('_')
                if len(parts) >= 3:
                    timestamp_str = f"{parts[-2]}_{parts[-1]}"
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if file_date >= cutoff_date:
                        with open(report_file) as f:
                            result = json.load(f)
                            agent_name = result.get('suite_name', 'unknown')
                            result['file_date'] = file_date.isoformat()
                            agent_data[agent_name].append(result)
            except Exception:
                continue
        
        # Collect multi-agent results
        for report_file in self.reports_dir.glob("multi_agent_*.json"):
            try:
                # Extract timestamp from filename
                parts = report_file.stem.split('_')
                if len(parts) >= 3:
                    timestamp_str = f"{parts[-2]}_{parts[-1]}"
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if file_date >= cutoff_date:
                        with open(report_file) as f:
                            result = json.load(f)
                            result['file_date'] = file_date.isoformat()
                            agent_data['multi_agent'].append(result)
            except Exception:
                continue
        
        # Sort each agent's data by date
        for agent in agent_data:
            agent_data[agent].sort(key=lambda x: x['file_date'])
        
        return dict(agent_data)
    
    def calculate_quality_trends(self, agent_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Calculate quality trends for each agent"""
        trends = {}
        
        for agent, evaluations in agent_data.items():
            if agent == 'multi_agent' or len(evaluations) < 2:
                continue
                
            # Get first and last scores
            first_score = evaluations[0]['weighted_score']
            last_score = evaluations[-1]['weighted_score']
            
            # Calculate trend
            trend_direction = "improving" if last_score > first_score else "degrading" if last_score < first_score else "stable"
            trend_magnitude = abs(last_score - first_score)
            
            # Calculate average score
            avg_score = sum(e['weighted_score'] for e in evaluations) / len(evaluations)
            
            # Identify problem areas
            recent_failures = []
            if evaluations[-1]['failed_tests'] > 0:
                recent_failures = [
                    test['test_id'] for test in evaluations[-1].get('test_results', [])
                    if not test.get('success', True)
                ]
            
            trends[agent] = {
                'first_score': first_score,
                'last_score': last_score,
                'avg_score': avg_score,
                'trend_direction': trend_direction,
                'trend_magnitude': trend_magnitude,
                'evaluations_count': len(evaluations),
                'recent_failures': recent_failures,
                'status': self._assess_agent_status(last_score, trend_direction, trend_magnitude)
            }
        
        return trends
    
    def _assess_agent_status(self, score: float, direction: str, magnitude: float) -> str:
        """Assess overall agent status"""
        if score >= 0.85:
            return "excellent"
        elif score >= 0.75 and direction != "degrading":
            return "good"
        elif score >= 0.65 and direction == "improving":
            return "improving"
        elif score >= 0.65:
            return "needs_attention"
        else:
            return "critical"
    
    def generate_weekly_report(self, days_back: int = 7) -> str:
        """Generate comprehensive weekly quality report"""
        
        agent_data = self.get_weekly_data(days_back)
        trends = self.calculate_quality_trends(agent_data)
        
        report_lines = [
            f"📊 Weekly Quality Report - {datetime.now().strftime('%B %d, %Y')}",
            "=" * 70,
            ""
        ]
        
        if not agent_data:
            report_lines.extend([
                "📋 No evaluation data found for the last 7 days",
                "🔄 Run: just eval-all to generate baseline data",
                ""
            ])
            return "\n".join(report_lines)
        
        # Overall summary
        total_agents = len(trends)
        excellent_agents = sum(1 for t in trends.values() if t['status'] == 'excellent')
        critical_agents = sum(1 for t in trends.values() if t['status'] == 'critical')
        
        report_lines.extend([
            f"📈 **System Overview:**",
            f"  • Total Agents: {total_agents}",
            f"  • Excellent: {excellent_agents} ({excellent_agents/total_agents:.1%})",
            f"  • Critical: {critical_agents} ({critical_agents/total_agents:.1%})",
            ""
        ])
        
        # Per-agent trends
        if trends:
            report_lines.extend([
                "🎯 **Agent Performance Trends:**"
            ])
            
            # Sort by status priority (critical first, excellent last)
            status_priority = {'critical': 0, 'needs_attention': 1, 'improving': 2, 'good': 3, 'excellent': 4}
            sorted_agents = sorted(trends.items(), key=lambda x: status_priority.get(x[1]['status'], 5))
            
            for agent, trend in sorted_agents:
                status_emoji = {
                    'excellent': '🌟',
                    'good': '✅', 
                    'improving': '📈',
                    'needs_attention': '⚠️',
                    'critical': '🚨'
                }[trend['status']]
                
                direction_arrow = {
                    'improving': '↗️',
                    'degrading': '↘️', 
                    'stable': '→'
                }[trend['trend_direction']]
                
                report_lines.append(
                    f"  {status_emoji} **{agent}**: {trend['first_score']:.2f} → {trend['last_score']:.2f} "
                    f"{direction_arrow} ({trend['evaluations_count']} evals)"
                )
                
                if trend['recent_failures']:
                    report_lines.append(f"    ❌ Recent failures: {', '.join(trend['recent_failures'][:3])}")
            
            report_lines.append("")
        
        # Critical issues
        critical_agents = [agent for agent, trend in trends.items() if trend['status'] == 'critical']
        if critical_agents:
            report_lines.extend([
                "🚨 **Critical Issues Requiring Immediate Attention:**",
                *[f"  • {agent}: Score {trends[agent]['last_score']:.2f} (threshold: 0.65)" for agent in critical_agents],
                ""
            ])
        
        # Improvement recommendations
        recommendations = self._generate_recommendations(trends)
        if recommendations:
            report_lines.extend([
                "💡 **Recommendations for This Week:**",
                *[f"  • {rec}" for rec in recommendations],
                ""
            ])
        
        # Quick actions
        report_lines.extend([
            "⚡ **Quick Actions:**",
            "  • `just eval-all` - Run all agent evaluations",
            "  • `just eval-run <agent>` - Test specific agent",
            "  • `just quality-dashboard` - Visual quality trends",
            "",
            f"📅 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ])
        
        return "\n".join(report_lines)
    
    def _generate_recommendations(self, trends: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on trends"""
        recommendations = []
        
        # Find agents with declining quality
        degrading_agents = [
            agent for agent, trend in trends.items() 
            if trend['trend_direction'] == 'degrading' and trend['trend_magnitude'] > 0.05
        ]
        
        if degrading_agents:
            recommendations.append(f"Investigate quality decline in: {', '.join(degrading_agents)}")
        
        # Find agents with low scores
        low_score_agents = [
            agent for agent, trend in trends.items()
            if trend['last_score'] < 0.70
        ]
        
        if low_score_agents:
            recommendations.append(f"Focus improvement efforts on: {', '.join(low_score_agents)}")
        
        # Find agents that are improving
        improving_agents = [
            agent for agent, trend in trends.items()
            if trend['trend_direction'] == 'improving' and trend['trend_magnitude'] > 0.10
        ]
        
        if improving_agents:
            recommendations.append(f"Apply successful patterns from: {', '.join(improving_agents)}")
        
        # General recommendations
        avg_score = sum(t['last_score'] for t in trends.values()) / len(trends) if trends else 0
        if avg_score < 0.75:
            recommendations.append("Consider lowering quality thresholds or improving test suites")
        
        return recommendations

def generate_weekly_report(days_back: int = 7) -> str:
    """Main entry point for weekly report generation"""
    reporter = WeeklyQualityReporter()
    return reporter.generate_weekly_report(days_back)

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Weekly quality reporting")
    parser.add_argument("--days", type=int, default=7, help="Days to include in report")
    parser.add_argument("--agent", help="Generate report for specific agent")
    
    args = parser.parse_args()
    
    if args.agent:
        # Single agent report (could be implemented)
        print(f"📊 Single agent reports not yet implemented for {args.agent}")
        print("🔄 Use: just eval-run {args.agent} for now")
    else:
        report = generate_weekly_report(args.days)
        print(report)

if __name__ == "__main__":
    main()