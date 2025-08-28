"""
CI-Safe Achievement Tracker

This module provides a simplified, CI-safe achievement tracking system
that doesn't rely on complex service imports and works reliably in GitHub Actions.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import Json

logger = logging.getLogger(__name__)


class CIAchievementTracker:
    """
    CI-safe achievement tracker that works in GitHub Actions environment.
    
    Uses direct database connections and minimal dependencies to avoid
    import errors in CI environments.
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        
        # Technology detection patterns
        self.tech_patterns = {
            'Python': ['.py', 'python', 'pip', 'pytest'],
            'TypeScript': ['.ts', '.tsx', 'typescript'],
            'JavaScript': ['.js', '.jsx', 'node', 'npm'],
            'Docker': ['Dockerfile', 'docker-compose', '.dockerignore'],
            'Kubernetes': ['k8s/', 'kubernetes/', '.yaml', 'helm/'],
            'FastAPI': ['fastapi', 'uvicorn', '@app.'],
            'SQLAlchemy': ['sqlalchemy', 'alembic', 'models.py'],
            'Testing': ['test_', 'tests/', 'pytest', 'unittest'],
            'CI/CD': ['.github/workflows/', 'github-actions'],
            'Database': ['migration', 'schema', 'models.py', 'db/'],
            'Machine Learning': ['ml', 'model', 'algorithm', 'statistical'],
            'API Design': ['endpoint', 'router', 'api/', 'routes/'],
            'Monitoring': ['prometheus', 'grafana', 'metrics', 'observability']
        }
        
        # Business impact keywords
        self.business_keywords = {
            'performance': ['performance', 'optimization', 'faster', 'speed', 'latency'],
            'cost_reduction': ['cost', 'reduce', 'efficient', 'savings'],
            'user_experience': ['ui', 'ux', 'user experience', 'usability'],
            'security': ['security', 'vulnerability', 'auth', 'encryption'],
            'automation': ['automation', 'automated', 'workflow', 'pipeline'],
            'scalability': ['scale', 'scalable', 'distributed', 'cluster'],
            'reliability': ['reliability', 'stable', 'robust', 'error handling']
        }
    
    def analyze_pr_data(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze PR data to extract comprehensive metrics."""
        
        # Extract technology stack
        tech_stack = self._extract_tech_stack(pr_data)
        
        # Extract business impact indicators
        business_impact = self._analyze_business_impact(pr_data)
        
        # Calculate scores
        impact_score = self._calculate_impact_score(pr_data, tech_stack, business_impact)
        complexity_score = self._calculate_complexity_score(pr_data, tech_stack)
        
        # Determine category
        category = self._determine_category(pr_data, business_impact)
        
        # Calculate business value
        business_value = self._calculate_business_value(impact_score, complexity_score, business_impact)
        
        return {
            'tech_stack': tech_stack,
            'business_impact': business_impact,
            'impact_score': impact_score,
            'complexity_score': complexity_score,
            'category': category,
            'business_value': business_value,
            'skills_demonstrated': self._extract_skills(pr_data, tech_stack),
            'time_saved_estimate': max(1.0, complexity_score / 20.0),
            'performance_improvement': 10.0 if business_impact.get('affects_performance') else 0.0
        }
    
    def _extract_tech_stack(self, pr_data: Dict[str, Any]) -> List[str]:
        """Extract technology stack from PR data."""
        tech_stack = set()
        
        # Analyze from existing tech_stack if available
        if 'tech_stack' in pr_data:
            tech_stack.update(pr_data['tech_stack'])
        
        # Analyze title and body
        content = f"{pr_data.get('title', '')} {pr_data.get('body', '')}".lower()
        
        for tech, patterns in self.tech_patterns.items():
            if any(pattern.lower() in content for pattern in patterns):
                tech_stack.add(tech)
        
        # Analyze files if available
        files = pr_data.get('files', [])
        for file_info in files:
            filename = file_info.get('filename', '').lower()
            for tech, patterns in self.tech_patterns.items():
                if any(pattern in filename for pattern in patterns):
                    tech_stack.add(tech)
        
        return list(tech_stack)[:10]  # Limit to top 10
    
    def _analyze_business_impact(self, pr_data: Dict[str, Any]) -> Dict[str, bool]:
        """Analyze business impact from PR content."""
        content = f"{pr_data.get('title', '')} {pr_data.get('body', '')}".lower()
        
        impact = {}
        for impact_type, keywords in self.business_keywords.items():
            impact[f'affects_{impact_type}'] = any(keyword in content for keyword in keywords)
        
        # Add categorical analysis
        title = pr_data.get('title', '').lower()
        impact['is_feature'] = title.startswith('feat')
        impact['is_bugfix'] = title.startswith('fix')
        impact['is_breaking_change'] = 'breaking change' in content
        impact['affects_api'] = any(word in content for word in ['api', 'endpoint', 'route'])
        
        return impact
    
    def _calculate_impact_score(self, pr_data: Dict[str, Any], tech_stack: List[str], business_impact: Dict[str, bool]) -> int:
        """Calculate comprehensive impact score."""
        base_score = 60  # Start higher for any merged PR
        
        # Size impact
        total_changes = pr_data.get('additions', 0) + pr_data.get('deletions', 0)
        if total_changes >= 1000: base_score += 25
        elif total_changes >= 500: base_score += 15
        elif total_changes >= 200: base_score += 10
        elif total_changes >= 50: base_score += 5
        
        # Technology diversity
        if len(tech_stack) >= 5: base_score += 15
        elif len(tech_stack) >= 3: base_score += 10
        elif len(tech_stack) >= 2: base_score += 5
        
        # Business impact bonuses
        if business_impact.get('affects_performance'): base_score += 15
        if business_impact.get('affects_security'): base_score += 15
        if business_impact.get('affects_automation'): base_score += 10
        if business_impact.get('affects_cost_reduction'): base_score += 10
        if business_impact.get('is_feature'): base_score += 10
        if business_impact.get('is_breaking_change'): base_score += 20
        
        return min(base_score, 100)
    
    def _calculate_complexity_score(self, pr_data: Dict[str, Any], tech_stack: List[str]) -> int:
        """Calculate technical complexity score."""
        complexity = 50
        
        # Code volume complexity
        total_changes = pr_data.get('additions', 0) + pr_data.get('deletions', 0)
        if total_changes >= 1000: complexity += 20
        elif total_changes >= 500: complexity += 15
        elif total_changes >= 200: complexity += 10
        
        # File complexity
        files = pr_data.get('changed_files', 0)
        if files >= 20: complexity += 15
        elif files >= 10: complexity += 10
        elif files >= 5: complexity += 5
        
        # Technology complexity
        advanced_tech = {'Machine Learning', 'Statistical Analysis', 'Kubernetes', 'Database'}
        if any(tech in advanced_tech for tech in tech_stack):
            complexity += 15
        
        # Service complexity (if multiple services modified)
        services = pr_data.get('services_modified', [])
        if len(services) >= 3: complexity += 15
        elif len(services) >= 2: complexity += 10
        
        return min(complexity, 100)
    
    def _determine_category(self, pr_data: Dict[str, Any], business_impact: Dict[str, bool]) -> str:
        """Determine achievement category."""
        title = pr_data.get('title', '').lower()
        
        if business_impact.get('is_feature') or 'feat' in title:
            return 'feature'
        elif business_impact.get('is_bugfix') or 'fix' in title:
            return 'bugfix'
        elif 'test' in title or 'testing' in title:
            return 'testing'
        elif business_impact.get('affects_performance') or 'optimization' in title:
            return 'optimization'
        elif business_impact.get('affects_security'):
            return 'security'
        elif business_impact.get('affects_automation'):
            return 'infrastructure'
        else:
            return 'feature'
    
    def _calculate_business_value(self, impact_score: int, complexity_score: int, business_impact: Dict[str, bool]) -> str:
        """Calculate estimated business value."""
        # Base calculation
        base_value = max(5000, complexity_score * 100)
        
        # Business multipliers
        multiplier = 1.0
        if business_impact.get('affects_performance'): multiplier *= 1.5
        if business_impact.get('affects_automation'): multiplier *= 1.4
        if business_impact.get('affects_security'): multiplier *= 1.3
        if business_impact.get('affects_cost_reduction'): multiplier *= 1.2
        if business_impact.get('is_breaking_change'): multiplier *= 1.6
        
        estimated_value = int(base_value * multiplier)
        
        return json.dumps({
            "total_value": estimated_value,
            "currency": "USD",
            "period": "yearly",
            "type": "automation",
            "confidence": 0.9,
            "method": "automation_heuristic",
            "breakdown": {
                "complexity_factor": complexity_score * 100,
                "base_value": 5000,
                "multiplier": multiplier
            }
        })
    
    def _extract_skills(self, pr_data: Dict[str, Any], tech_stack: List[str]) -> List[str]:
        """Extract demonstrated skills from PR data."""
        skills = set(tech_stack)
        
        # Add general skills based on PR characteristics
        if pr_data.get('changed_files', 0) >= 10:
            skills.add('Code Review')
        if pr_data.get('commits', 0) >= 5:
            skills.add('Git')
        
        # Add collaboration skills
        skills.add('Collaboration')
        skills.add('Automated Testing')
        
        return list(skills)[:15]  # Limit to 15 skills
    
    def create_achievement_from_pr(self, pr_data: Dict[str, Any]) -> bool:
        """Create achievement record from PR data."""
        try:
            # Analyze PR data
            analysis = self.analyze_pr_data(pr_data)
            
            # Connect to database
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Check if already exists
            cursor.execute(
                "SELECT id FROM achievements WHERE source_type = 'github_pr' AND source_id = %s",
                (str(pr_data['pr_number']),)
            )
            
            if cursor.fetchone():
                logger.info(f"Achievement already exists for PR #{pr_data['pr_number']}")
                return True
            
            # Calculate timing
            created = datetime.fromisoformat(pr_data['created_at'].replace('Z', '+00:00'))
            merged = datetime.fromisoformat(pr_data['merged_at'].replace('Z', '+00:00'))
            duration_hours = (merged - created).total_seconds() / 3600
            
            # Build evidence
            evidence = {
                "pr_metrics": {
                    "additions": pr_data.get('additions', 0),
                    "deletions": pr_data.get('deletions', 0),
                    "files_changed": pr_data.get('changed_files', 0),
                    "commits": pr_data.get('commits', 0)
                },
                "analysis": analysis,
                "ci_collection": {
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                    "method": "github_actions_ci"
                }
            }
            
            # Create achievement
            insert_sql = """
                INSERT INTO achievements (
                    title, description, category, started_at, completed_at, duration_hours,
                    impact_score, complexity_score, business_value, time_saved_hours,
                    performance_improvement_pct, source_type, source_id, source_url,
                    evidence, tags, skills_demonstrated, ai_summary,
                    portfolio_ready, portfolio_section, display_priority,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            source_url = f"https://github.com/{os.getenv('GITHUB_REPOSITORY', 'unknown')}/pull/{pr_data['pr_number']}"
            
            cursor.execute(insert_sql, (
                f"Shipped: {pr_data['title']}",
                pr_data.get('body', '')[:1000],
                analysis['category'],
                created,
                merged,
                duration_hours,
                analysis['impact_score'],
                analysis['complexity_score'],
                analysis['business_value'],
                analysis['time_saved_estimate'],
                analysis['performance_improvement'],
                'github_pr',
                str(pr_data['pr_number']),
                source_url,
                Json(evidence),
                Json(pr_data.get('labels', [])),
                Json(analysis['skills_demonstrated']),
                f"Delivered {analysis['category']} changes with {len(analysis['tech_stack'])} technologies",
                analysis['impact_score'] >= 70,
                'engineering',
                analysis['impact_score'],
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            ))
            
            conn.commit()
            
            logger.info(f"✅ Created achievement for PR #{pr_data['pr_number']}")
            logger.info(f"   Impact: {analysis['impact_score']}, Complexity: {analysis['complexity_score']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create achievement: {e}")
            if 'conn' in locals():
                conn.rollback()
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()


def main():
    """Main function for CI execution."""
    # Get environment variables
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not configured")
        sys.exit(1)
    
    # Get PR data from environment (set by GitHub Actions)
    pr_data_raw = os.getenv('PR_METRICS_JSON', '{}')
    
    try:
        pr_data = json.loads(pr_data_raw)
        if not pr_data or 'pr_number' not in pr_data:
            print("⚠️  No valid PR data available")
            return
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse PR data: {e}")
        sys.exit(1)
    
    # Create tracker and process
    tracker = CIAchievementTracker(database_url)
    success = tracker.create_achievement_from_pr(pr_data)
    
    if success:
        print("🏆 Achievement tracking completed successfully!")
    else:
        print("❌ Achievement tracking failed")
        sys.exit(1)


if __name__ == "__main__":
    main()