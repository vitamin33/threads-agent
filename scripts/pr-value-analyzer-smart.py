#!/usr/bin/env python3
"""
Smart PR Value Analyzer with Deduplication
Only analyzes when needed, tracks history
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Tuple

# Import the ultimate analyzer for actual analysis
try:
    from pr_value_analyzer_ultimate import PRValueAnalyzer
except ImportError:
    print("Error: Could not import pr_value_analyzer_ultimate.py")
    print("Make sure the file exists in the same directory")
    sys.exit(1)

class SmartPRAnalyzer:
    """Smart wrapper around PR analyzer with deduplication"""
    
    def __init__(self):
        self.analyzer = PRValueAnalyzer()
        self.history_file = Path('.pr_analysis_history.json')
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        """Load analysis history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_history(self):
        """Save analysis history"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def _get_pr_info(self, pr_number: int) -> Optional[Dict]:
        """Get PR info using GitHub CLI"""
        try:
            result = subprocess.run(
                ['gh', 'pr', 'view', str(pr_number), '--json', 
                 'number,title,state,commits,author,createdAt,updatedAt,headRefOid'],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except:
            return None
    
    def _get_analysis_key(self, pr_number: int, commit_sha: str) -> str:
        """Get unique key for PR analysis"""
        return f"pr_{pr_number}_{commit_sha[:7]}"
    
    def should_analyze(self, pr_number: int, force: bool = False) -> Tuple[bool, str]:
        """Check if PR should be analyzed"""
        if force:
            return True, "Force flag set"
        
        # Get current PR info
        pr_info = self._get_pr_info(pr_number)
        if not pr_info:
            return True, "Could not fetch PR info"
        
        # Get current commit SHA
        current_sha = pr_info.get('headRefOid', '')
        if not current_sha:
            return True, "Could not determine current SHA"
        
        # Check history
        key = self._get_analysis_key(pr_number, current_sha)
        if key in self.history:
            last_analysis = self.history[key]
            analysis_time = last_analysis.get('timestamp', 'unknown')
            return False, f"Already analyzed at {analysis_time} for SHA {current_sha[:7]}"
        
        # Check if PR was updated since last analysis
        pr_key = f"pr_{pr_number}"
        if pr_key in self.history:
            last_sha = self.history[pr_key].get('last_sha', '')
            if last_sha != current_sha[:7]:
                return True, f"PR updated from {last_sha} to {current_sha[:7]}"
        
        return True, "No previous analysis found"
    
    def analyze(self, pr_number: int, force: bool = False) -> Optional[Dict]:
        """Analyze PR if needed"""
        should_analyze, reason = self.should_analyze(pr_number, force)
        
        print(f"\n🔍 Checking PR #{pr_number}")
        print(f"   Status: {'Will analyze' if should_analyze else 'Skip analysis'}")
        print(f"   Reason: {reason}")
        
        if not should_analyze and not force:
            # Load and return cached analysis
            pr_info = self._get_pr_info(pr_number)
            if pr_info:
                key = self._get_analysis_key(pr_number, pr_info['headRefOid'])
                if key in self.history:
                    print(f"   Using cached analysis from {self.history[key].get('timestamp')}")
                    return self.history[key].get('analysis')
            return None
        
        # Perform new analysis
        print(f"\n📊 Analyzing PR #{pr_number}...")
        analysis = self.analyzer.analyze_pr(pr_number)
        
        if analysis:
            # Get PR info for history
            pr_info = self._get_pr_info(pr_number)
            if pr_info:
                current_sha = pr_info.get('headRefOid', '')
                key = self._get_analysis_key(pr_number, current_sha)
                
                # Store in history
                self.history[key] = {
                    'timestamp': datetime.now().isoformat(),
                    'pr_number': pr_number,
                    'sha': current_sha[:7],
                    'title': pr_info.get('title', ''),
                    'analysis': analysis
                }
                
                # Also store latest for this PR
                self.history[f"pr_{pr_number}"] = {
                    'last_sha': current_sha[:7],
                    'last_analysis': datetime.now().isoformat()
                }
                
                self._save_history()
                print(f"✅ Analysis complete and cached for SHA {current_sha[:7]}")
        
        return analysis
    
    def get_pr_analysis_summary(self, pr_number: int) -> Dict:
        """Get summary of all analyses for a PR"""
        summary = {
            'pr_number': pr_number,
            'analyses': [],
            'latest': None
        }
        
        # Find all analyses for this PR
        for key, data in self.history.items():
            if key.startswith(f"pr_{pr_number}_") and 'analysis' in data:
                summary['analyses'].append({
                    'sha': data['sha'],
                    'timestamp': data['timestamp'],
                    'portfolio_value': data['analysis'].get('summary', {}).get('portfolio_value', 0)
                })
        
        # Sort by timestamp
        summary['analyses'].sort(key=lambda x: x['timestamp'], reverse=True)
        
        if summary['analyses']:
            summary['latest'] = summary['analyses'][0]
        
        return summary

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: pr-value-analyzer-smart.py <pr_number> [--force] [--summary]")
        sys.exit(1)
    
    pr_number = int(sys.argv[1])
    force = '--force' in sys.argv
    show_summary = '--summary' in sys.argv
    
    analyzer = SmartPRAnalyzer()
    
    if show_summary:
        # Show analysis history for PR
        summary = analyzer.get_pr_analysis_summary(pr_number)
        print(f"\n📊 Analysis History for PR #{pr_number}")
        print(f"   Total analyses: {len(summary['analyses'])}")
        
        for analysis in summary['analyses']:
            print(f"   - SHA {analysis['sha']}: ${analysis['portfolio_value']:,.0f} ({analysis['timestamp']})")
        
        return
    
    # Perform analysis
    result = analyzer.analyze(pr_number, force)
    
    if result:
        # Save standard output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main analysis
        output_file = f"pr_{pr_number}_value_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n📄 Analysis saved to: {output_file}")
        
        # Create achievement file if achievement data exists
        if 'achievement_data' in result:
            achievement_dir = Path('.achievements')
            achievement_dir.mkdir(exist_ok=True)
            
            achievement_file = achievement_dir / f"pr_{pr_number}_achievement.json"
            with open(achievement_file, 'w') as f:
                json.dump(result['achievement_data'], f, indent=2)
            print(f"🏆 Achievement saved to: {achievement_file}")
        
        # Print summary
        if 'summary' in result:
            summary = result['summary']
            print(f"\n✨ PR #{pr_number} Analysis Summary:")
            print(f"   Portfolio Value: ${summary.get('portfolio_value', 0):,.0f}")
            print(f"   ROI: {summary.get('roi_percent', 0)}%")
            print(f"   Overall Score: {summary.get('overall_score', 0)}/10")
            print(f"   Confidence: {summary.get('confidence', 'medium')}")
    else:
        print("\n⚠️  No analysis performed (already up to date or error occurred)")

if __name__ == "__main__":
    main()