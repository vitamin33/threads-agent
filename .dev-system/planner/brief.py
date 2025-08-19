"""
M5: AI-Powered Morning Brief System
Data-driven daily planning using M1 telemetry + M2 quality data
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

from ops.telemetry import get_daily_metrics

@dataclass
class Priority:
    """Single prioritized task with ICE scoring"""
    title: str
    description: str
    impact: float      # 1-10 scale
    confidence: float  # 1-10 scale  
    effort: float      # 1-10 scale (lower = less effort)
    ice_score: float   # Calculated ICE score
    data_source: str   # What data informed this priority
    action: str        # Specific next action

class MorningBriefGenerator:
    """Generates data-driven morning briefs using telemetry and quality data"""
    
    def __init__(self):
        self.telemetry_data = None
        self.quality_data = None
        self.git_data = None
        
    def load_data_sources(self):
        """Load all data sources for brief generation"""
        # M1 Telemetry data
        try:
            self.telemetry_data = get_daily_metrics(7)  # Last 7 days
        except Exception as e:
            print(f"⚠️  Telemetry data unavailable: {e}")
            self.telemetry_data = self._get_fallback_telemetry()
        
        # M2 Quality data
        self.quality_data = self._load_recent_evaluations()
        
        # Git activity data
        self.git_data = self._analyze_git_activity()
        
    def _get_fallback_telemetry(self) -> Dict[str, Any]:
        """Fallback telemetry data when M1 not available"""
        return {
            'success_rate': 0.95,
            'p95_latency_ms': 1200.0,
            'total_cost': 2.50,
            'top_agent': 'persona_runtime',
            'failed_calls': 5,
            'alerts': []
        }
    
    def _load_recent_evaluations(self) -> Dict[str, Any]:
        """Load recent M2 evaluation results"""
        reports_dir = DEV_SYSTEM_ROOT / "evals" / "reports"
        
        if not reports_dir.exists():
            return {'recent_evaluations': [], 'latest_score': 0.85}
        
        try:
            # Find most recent evaluation
            eval_files = list(reports_dir.glob("eval_*.json"))
            if not eval_files:
                return {'recent_evaluations': [], 'latest_score': 0.85}
            
            # Get latest file
            latest_file = max(eval_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_file) as f:
                latest_eval = json.load(f)
            
            return {
                'recent_evaluations': [latest_eval],
                'latest_score': latest_eval.get('weighted_score', 0.85),
                'latest_status': latest_eval.get('gate_status', 'UNKNOWN'),
                'failed_tests': latest_eval.get('failed_tests', 0)
            }
            
        except Exception as e:
            print(f"⚠️  Quality data unavailable: {e}")
            return {'recent_evaluations': [], 'latest_score': 0.85}
    
    def _analyze_git_activity(self) -> Dict[str, Any]:
        """Analyze recent git activity"""
        import subprocess
        
        try:
            # Commits in last 24 hours
            result = subprocess.run([
                'git', 'log', '--since=24 hours ago', '--oneline'
            ], capture_output=True, text=True, cwd=DEV_SYSTEM_ROOT.parent)
            
            commits_today = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # Current branch
            result = subprocess.run([
                'git', 'branch', '--show-current'
            ], capture_output=True, text=True, cwd=DEV_SYSTEM_ROOT.parent)
            
            current_branch = result.stdout.strip()
            
            # Files changed recently
            result = subprocess.run([
                'git', 'diff', '--name-only', 'HEAD~5..HEAD'
            ], capture_output=True, text=True, cwd=DEV_SYSTEM_ROOT.parent)
            
            changed_files = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            return {
                'commits_today': commits_today,
                'current_branch': current_branch,
                'changed_files': changed_files,
                'branch_type': self._classify_branch_type(current_branch)
            }
            
        except Exception as e:
            print(f"⚠️  Git data unavailable: {e}")
            return {
                'commits_today': 0,
                'current_branch': 'unknown',
                'changed_files': 0,
                'branch_type': 'maintenance'
            }
    
    def _classify_branch_type(self, branch_name: str) -> str:
        """Classify branch type for context-aware planning"""
        if 'feat' in branch_name:
            return 'feature_development'
        elif 'fix' in branch_name:
            return 'bug_fixing'
        elif 'refactor' in branch_name:
            return 'refactoring'
        elif 'test' in branch_name:
            return 'testing'
        elif 'docs' in branch_name:
            return 'documentation'
        else:
            return 'maintenance'
    
    def calculate_ice_score(self, impact: float, confidence: float, effort: float) -> float:
        """Calculate ICE score with configurable weights"""
        # Load weights from config
        config_path = DEV_SYSTEM_ROOT / "config" / "dev-system.yaml"
        weights = {'impact': 0.5, 'confidence': 0.3, 'effort': 0.2}  # Default
        
        try:
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)
                weights = config.get('planning', {}).get('ice_weights', weights)
        except:
            pass
        
        # ICE = (Impact × Confidence) / Effort with weights
        ice_score = (
            (impact * weights['impact']) * 
            (confidence * weights['confidence']) / 
            (effort * weights['effort'])
        )
        
        return round(ice_score, 2)
    
    def generate_priorities(self) -> List[Priority]:
        """Generate prioritized tasks based on all data sources"""
        priorities = []
        
        # Priority 1: Address performance issues (if any)
        if self.telemetry_data and self.telemetry_data.get('alerts'):
            for alert in self.telemetry_data['alerts']:
                priorities.append(Priority(
                    title="Fix Performance Alert",
                    description=f"Address: {alert}",
                    impact=9.0,  # High impact - affects daily work
                    confidence=8.0,  # High confidence - data-driven
                    effort=3.0,  # Usually quick fixes
                    ice_score=self.calculate_ice_score(9.0, 8.0, 3.0),
                    data_source="M1 Telemetry",
                    action=f"Investigate alert: {alert}"
                ))
        
        # Priority 2: Address quality issues (if any)
        if self.quality_data and self.quality_data.get('latest_status') == 'FAIL':
            failed_tests = self.quality_data.get('failed_tests', 0)
            priorities.append(Priority(
                title="Fix Quality Gate Failures",
                description=f"Resolve {failed_tests} failing quality tests",
                impact=8.0,  # High impact - blocks merges
                confidence=9.0,  # High confidence - explicit failures
                effort=4.0,  # Moderate effort
                ice_score=self.calculate_ice_score(8.0, 9.0, 4.0),
                data_source="M2 Quality Gates",
                action="Run: just eval-latest to see failures"
            ))
        
        # Priority 3: Continue branch-specific work
        branch_type = self.git_data.get('branch_type', 'maintenance')
        branch_priorities = self._get_branch_specific_priorities(branch_type)
        priorities.extend(branch_priorities)
        
        # Priority 4: Optimize based on telemetry insights
        if self.telemetry_data:
            optimization_priorities = self._get_optimization_priorities()
            priorities.extend(optimization_priorities)
        
        # Priority 5: Development system improvements
        system_priorities = self._get_system_improvement_priorities()
        priorities.extend(system_priorities)
        
        # Sort by ICE score (highest first)
        priorities.sort(key=lambda p: p.ice_score, reverse=True)
        
        return priorities[:5]  # Top 5 priorities
    
    def _get_branch_specific_priorities(self, branch_type: str) -> List[Priority]:
        """Get priorities based on current branch type"""
        branch_priorities = {
            'feature_development': [
                Priority(
                    title="Complete Feature Implementation",
                    description="Finish current feature development and testing",
                    impact=8.0, confidence=7.0, effort=6.0,
                    ice_score=self.calculate_ice_score(8.0, 7.0, 6.0),
                    data_source="Git Branch Analysis",
                    action="Continue feature implementation"
                )
            ],
            'bug_fixing': [
                Priority(
                    title="Verify Bug Fixes",
                    description="Test and validate recent bug fixes",
                    impact=9.0, confidence=8.0, effort=3.0,
                    ice_score=self.calculate_ice_score(9.0, 8.0, 3.0),
                    data_source="Git Branch Analysis", 
                    action="Run regression tests"
                )
            ],
            'refactoring': [
                Priority(
                    title="Complete Refactoring",
                    description="Finish code refactoring and update tests",
                    impact=6.0, confidence=7.0, effort=5.0,
                    ice_score=self.calculate_ice_score(6.0, 7.0, 5.0),
                    data_source="Git Branch Analysis",
                    action="Complete refactoring milestone"
                )
            ]
        }
        
        return branch_priorities.get(branch_type, [])
    
    def _get_optimization_priorities(self) -> List[Priority]:
        """Get optimization priorities based on telemetry data"""
        priorities = []
        
        # Check for high latency
        if self.telemetry_data['p95_latency_ms'] > 2000:
            priorities.append(Priority(
                title="Optimize Performance",
                description=f"P95 latency is {self.telemetry_data['p95_latency_ms']:.0f}ms",
                impact=7.0, confidence=8.0, effort=5.0,
                ice_score=self.calculate_ice_score(7.0, 8.0, 5.0),
                data_source="M1 Telemetry",
                action="Profile slowest operations"
            ))
        
        # Check for high costs
        if self.telemetry_data['total_cost'] > 5.0:
            priorities.append(Priority(
                title="Optimize Token Usage",
                description=f"Daily cost is ${self.telemetry_data['total_cost']:.2f}",
                impact=6.0, confidence=8.0, effort=4.0,
                ice_score=self.calculate_ice_score(6.0, 8.0, 4.0),
                data_source="M1 Telemetry",
                action="Analyze expensive operations"
            ))
        
        return priorities
    
    def _get_system_improvement_priorities(self) -> List[Priority]:
        """Get development system improvement priorities"""
        return [
            Priority(
                title="Enhance Development System",
                description="Continue building top 1% agent factory",
                impact=8.0, confidence=9.0, effort=7.0,
                ice_score=self.calculate_ice_score(8.0, 9.0, 7.0),
                data_source="Milestone Roadmap",
                action="Continue with next milestone (M4/M3/M6)"
            )
        ]
    
    def generate_morning_brief(self) -> str:
        """Generate complete morning brief"""
        self.load_data_sources()
        priorities = self.generate_priorities()
        
        now = datetime.now()
        brief_lines = [
            f"🌅 Morning Brief - {now.strftime('%A, %B %d, %Y')}",
            "=" * 60,
            "",
            "📊 **Yesterday's Performance:**"
        ]
        
        # Add telemetry summary
        if self.telemetry_data:
            brief_lines.extend([
                f"  • Success Rate: {self.telemetry_data['success_rate']:.1%}",
                f"  • P95 Latency: {self.telemetry_data['p95_latency_ms']:.0f}ms",
                f"  • Cost: ${self.telemetry_data['total_cost']:.2f}",
                f"  • Top Agent: {self.telemetry_data['top_agent']}"
            ])
            
            if self.telemetry_data.get('alerts'):
                brief_lines.extend([
                    "",
                    "🚨 **Alerts:**",
                    *[f"  • {alert}" for alert in self.telemetry_data['alerts']]
                ])
        
        # Add quality summary
        if self.quality_data and self.quality_data.get('recent_evaluations'):
            brief_lines.extend([
                "",
                "🎯 **Quality Status:**",
                f"  • Latest Score: {self.quality_data['latest_score']:.2f}",
                f"  • Gate Status: {self.quality_data['latest_status']}",
                f"  • Failed Tests: {self.quality_data.get('failed_tests', 0)}"
            ])
        
        # Add git activity summary  
        if self.git_data:
            brief_lines.extend([
                "",
                "📝 **Recent Activity:**",
                f"  • Commits: {self.git_data['commits_today']}",
                f"  • Branch: {self.git_data['current_branch']}",
                f"  • Type: {self.git_data['branch_type'].replace('_', ' ').title()}"
            ])
        
        # Add top priorities
        brief_lines.extend([
            "",
            "🎯 **Top 3 Priorities Today:**"
        ])
        
        for i, priority in enumerate(priorities[:3], 1):
            brief_lines.extend([
                f"{i}. **{priority.title}** (ICE: {priority.ice_score})",
                f"   {priority.description}",
                f"   📋 Action: {priority.action}",
                f"   📊 Source: {priority.data_source}",
                ""
            ])
        
        # Add recommended commands
        brief_lines.extend([
            "⚡ **Quick Commands:**",
            "  • `just metrics-today` - Check yesterday's metrics",
            "  • `just eval-latest` - Check latest quality results", 
            "  • `just brief` - Regenerate this brief",
            "  • `just debrief` - Log evening outcomes (coming in M5)",
            "",
            "🎯 **Focus Time**: Block 2-3 hours for top priority",
            "💡 **Tip**: Use `just metrics-today` after major changes",
            "",
            f"Generated at {now.strftime('%H:%M')} using M1 telemetry + M2 quality data"
        ])
        
        return "\n".join(brief_lines)

def generate_morning_brief() -> str:
    """Main entry point for morning brief generation"""
    generator = MorningBriefGenerator()
    return generator.generate_morning_brief()

def save_brief_context(priorities: List[Priority]):
    """Save brief context for evening debrief correlation"""
    context_dir = DEV_SYSTEM_ROOT / "planner" / "context"
    context_dir.mkdir(exist_ok=True)
    
    today = datetime.now().strftime("%Y%m%d")
    context_file = context_dir / f"brief_{today}.json"
    
    context_data = {
        'date': today,
        'timestamp': datetime.now().isoformat(),
        'priorities': [
            {
                'title': p.title,
                'ice_score': p.ice_score,
                'action': p.action,
                'data_source': p.data_source
            } for p in priorities
        ]
    }
    
    with open(context_file, 'w') as f:
        json.dump(context_data, f, indent=2)

def main():
    """CLI entry point"""
    brief = generate_morning_brief()
    print(brief)
    
    # Also save context for evening correlation
    generator = MorningBriefGenerator()
    generator.load_data_sources()
    priorities = generator.generate_priorities()
    save_brief_context(priorities)

if __name__ == "__main__":
    main()