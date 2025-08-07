#!/usr/bin/env python3
"""
CI Performance Analyzer
Analyzes GitHub Actions run times and suggests optimizations
"""

import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

class CIPerformanceAnalyzer:
    """Analyze CI/CD performance and suggest improvements"""
    
    def __init__(self):
        self.workflows = [
            'dev-ci.yml',
            'quick-ci.yml', 
            'docker-ci.yml',
            'pr-value-analysis.yml'
        ]
    
    def get_workflow_runs(self, workflow: str, limit: int = 20) -> List[Dict]:
        """Get recent workflow runs"""
        try:
            result = subprocess.run([
                'gh', 'run', 'list',
                '--workflow', workflow,
                '--json', 'databaseId,status,conclusion,createdAt,updatedAt,name',
                '--limit', str(limit)
            ], capture_output=True, text=True, check=True)
            
            return json.loads(result.stdout)
        except:
            return []
    
    def calculate_duration(self, run: Dict) -> Optional[float]:
        """Calculate run duration in minutes"""
        try:
            created = datetime.fromisoformat(run['createdAt'].replace('Z', '+00:00'))
            updated = datetime.fromisoformat(run['updatedAt'].replace('Z', '+00:00'))
            duration = (updated - created).total_seconds() / 60
            return round(duration, 1)
        except:
            return None
    
    def analyze_workflow(self, workflow: str) -> Dict:
        """Analyze a single workflow performance"""
        runs = self.get_workflow_runs(workflow)
        if not runs:
            return {'error': 'No runs found'}
        
        # Calculate metrics
        durations = []
        success_count = 0
        
        for run in runs:
            duration = self.calculate_duration(run)
            if duration:
                durations.append(duration)
            if run.get('conclusion') == 'success':
                success_count += 1
        
        if not durations:
            return {'error': 'No duration data'}
        
        return {
            'workflow': workflow,
            'total_runs': len(runs),
            'success_rate': round(success_count / len(runs) * 100, 1),
            'avg_duration': round(sum(durations) / len(durations), 1),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'recent_duration': durations[0] if durations else None
        }
    
    def suggest_optimizations(self, metrics: Dict) -> List[str]:
        """Suggest optimizations based on metrics"""
        suggestions = []
        
        # Check average duration
        if metrics.get('avg_duration', 0) > 10:
            suggestions.append("⏱️  Consider parallelizing jobs - average runtime > 10 minutes")
        
        # Check success rate
        if metrics.get('success_rate', 100) < 90:
            suggestions.append("🔧 Low success rate - add retry logic or fix flaky tests")
        
        # Check variance
        if metrics.get('max_duration', 0) > metrics.get('min_duration', 0) * 2:
            suggestions.append("📊 High variance in run times - investigate caching")
        
        # Workflow-specific suggestions
        if 'dev-ci' in metrics.get('workflow', ''):
            if metrics.get('avg_duration', 0) > 5:
                suggestions.append("🚀 dev-ci: Consider skipping k3d for non-infra changes")
        
        if 'docker-ci' in metrics.get('workflow', ''):
            suggestions.append("🐳 docker-ci: Ensure using registry cache and buildkit")
        
        return suggestions
    
    def generate_report(self):
        """Generate performance report"""
        print("🏃 CI/CD Performance Analysis")
        print("=" * 60)
        
        all_metrics = []
        
        for workflow in self.workflows:
            print(f"\n📊 Analyzing {workflow}...")
            metrics = self.analyze_workflow(workflow)
            
            if 'error' in metrics:
                print(f"   ⚠️  {metrics['error']}")
                continue
            
            all_metrics.append(metrics)
            
            print(f"   • Runs analyzed: {metrics['total_runs']}")
            print(f"   • Success rate: {metrics['success_rate']}%")
            print(f"   • Average duration: {metrics['avg_duration']} min")
            print(f"   • Recent duration: {metrics['recent_duration']} min")
            print(f"   • Range: {metrics['min_duration']} - {metrics['max_duration']} min")
            
            # Get suggestions
            suggestions = self.suggest_optimizations(metrics)
            if suggestions:
                print("   💡 Suggestions:")
                for suggestion in suggestions:
                    print(f"      {suggestion}")
        
        # Overall recommendations
        print("\n🎯 Overall Recommendations:")
        print("=" * 60)
        
        total_avg = sum(m['avg_duration'] for m in all_metrics if 'avg_duration' in m)
        print(f"📈 Total average CI time: {total_avg:.1f} minutes")
        
        if total_avg > 15:
            print("\n🚨 High total CI time! Priority optimizations:")
            print("   1. Enable job concurrency and parallelization")
            print("   2. Implement smart caching strategies")
            print("   3. Skip unchanged service tests")
            print("   4. Use GitHub's larger runners for critical paths")
        
        print("\n✨ Quick wins implemented:")
        print("   • PR value analysis deduplication")
        print("   • Smart test skipping based on changes")
        print("   • Enhanced Docker layer caching")
        print("   • Parallel job execution")

def main():
    """Run the analyzer"""
    analyzer = CIPerformanceAnalyzer()
    analyzer.generate_report()

if __name__ == "__main__":
    main()