# PR Merge Achievement System - Simplified & Powerful

## Core Concept
Every merged PR automatically generates multiple achievement stories based on what was actually changed, storing rich data for future use.

## 1. Enhanced Database Design (Future-Proof)

```sql
-- Core achievement table remains, but we add PR-specific analysis
CREATE TABLE pr_achievements (
    id SERIAL PRIMARY KEY,
    achievement_id INTEGER REFERENCES achievements(id),
    pr_number INTEGER NOT NULL UNIQUE,
    
    -- PR metadata
    title TEXT NOT NULL,
    description TEXT,
    merge_timestamp TIMESTAMP NOT NULL,
    author VARCHAR(255) NOT NULL,
    reviewers JSONB DEFAULT '[]',
    
    -- Code analysis results
    code_analysis JSONB NOT NULL, -- Detailed breakdown of changes
    impact_analysis JSONB NOT NULL, -- Business/technical impact
    
    -- Generated stories
    stories JSONB NOT NULL, -- Multiple story types
    
    -- Metrics from CI/CD
    ci_metrics JSONB DEFAULT '{}',
    performance_metrics JSONB DEFAULT '{}',
    quality_metrics JSONB DEFAULT '{}',
    
    -- Evidence
    evidence_urls JSONB DEFAULT '{}',
    
    -- For future auto-posting
    posting_metadata JSONB DEFAULT '{
        "linkedin": {"posted": false, "post_id": null},
        "twitter": {"posted": false, "post_id": null},
        "portfolio": {"included": false, "section": null}
    }',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Story templates for different aspects
CREATE TABLE story_types (
    id SERIAL PRIMARY KEY,
    type_name VARCHAR(100) UNIQUE NOT NULL, -- 'performance', 'feature', 'bugfix', 'architecture', etc.
    detection_rules JSONB NOT NULL, -- Rules to detect if PR contains this type
    template JSONB NOT NULL, -- Template for generating story
    target_audiences JSONB DEFAULT '[]', -- ['technical', 'business', 'leadership']
    min_threshold JSONB DEFAULT '{}' -- Minimum criteria to generate story
);

-- Detailed code changes tracking
CREATE TABLE pr_code_changes (
    id SERIAL PRIMARY KEY,
    pr_achievement_id INTEGER REFERENCES pr_achievements(id),
    
    -- File-level analysis
    file_path TEXT NOT NULL,
    language VARCHAR(50),
    file_type VARCHAR(50), -- 'component', 'api', 'config', 'test', etc.
    
    -- Change metrics
    lines_added INTEGER DEFAULT 0,
    lines_deleted INTEGER DEFAULT 0,
    complexity_before FLOAT,
    complexity_after FLOAT,
    
    -- Semantic analysis
    functions_added JSONB DEFAULT '[]',
    functions_modified JSONB DEFAULT '[]',
    functions_deleted JSONB DEFAULT '[]',
    
    -- Impact classification
    impact_areas JSONB DEFAULT '[]', -- ['performance', 'security', 'ux', 'scalability']
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- KPI tracking per PR
CREATE TABLE pr_kpi_impacts (
    id SERIAL PRIMARY KEY,
    pr_achievement_id INTEGER REFERENCES pr_achievements(id),
    
    kpi_category VARCHAR(100) NOT NULL,
    kpi_name VARCHAR(255) NOT NULL,
    
    -- Measurements
    baseline_value NUMERIC,
    new_value NUMERIC,
    improvement_percentage NUMERIC,
    
    -- Confidence and source
    confidence_score FLOAT DEFAULT 0.5, -- 0-1 confidence in measurement
    measurement_source VARCHAR(100), -- 'ci_test', 'production', 'estimated'
    
    -- Business impact
    dollar_impact NUMERIC, -- Estimated financial impact
    time_saved_hours NUMERIC, -- Estimated time savings
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Evidence storage
CREATE TABLE pr_evidence (
    id SERIAL PRIMARY KEY,
    pr_achievement_id INTEGER REFERENCES pr_achievements(id),
    
    evidence_type VARCHAR(50) NOT NULL, -- 'screenshot', 'benchmark', 'diagram', 'metric'
    title VARCHAR(255),
    description TEXT,
    url TEXT NOT NULL,
    
    -- Context
    context JSONB DEFAULT '{}', -- When/where/why this evidence was collected
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_pr_achievements_pr_number ON pr_achievements(pr_number);
CREATE INDEX idx_pr_achievements_merge_timestamp ON pr_achievements(merge_timestamp);
CREATE INDEX idx_pr_code_changes_impact ON pr_code_changes USING GIN(impact_areas);
CREATE INDEX idx_pr_kpi_impacts_category ON pr_kpi_impacts(kpi_category);
CREATE INDEX idx_stories_jsonb ON pr_achievements USING GIN(stories);
```

## 2. Simplified CI Workflow (After PR Merge)

```yaml
# .github/workflows/pr-achievement-analyzer.yml

name: PR Achievement Analyzer

on:
  pull_request:
    types: [closed]

jobs:
  analyze-and-create-achievements:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for analysis
          
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
          
      - name: Analyze Code Changes
        id: code_analysis
        run: |
          python3 << 'EOF'
          import json
          import subprocess
          from pathlib import Path
          
          # Get diff statistics
          pr_number = ${{ github.event.pull_request.number }}
          base_sha = "${{ github.event.pull_request.base.sha }}"
          head_sha = "${{ github.event.pull_request.head.sha }}"
          
          # Analyze what changed
          analysis = {
              "files_by_type": {},
              "impact_areas": [],
              "complexity_changes": {},
              "test_coverage_delta": 0,
              "documentation_changes": False,
              "api_changes": False,
              "database_changes": False,
              "ui_changes": False,
              "performance_changes": False
          }
          
          # Get changed files
          diff_output = subprocess.run(
              ["git", "diff", "--name-status", f"{base_sha}...{head_sha}"],
              capture_output=True,
              text=True
          ).stdout
          
          for line in diff_output.strip().split('\n'):
              if line:
                  status, filepath = line.split('\t', 1)
                  path = Path(filepath)
                  
                  # Classify file
                  if path.suffix == '.py':
                      analysis["files_by_type"].setdefault("python", []).append(str(path))
                      
                      # Check for specific patterns
                      if 'api' in str(path) or 'routes' in str(path):
                          analysis["api_changes"] = True
                          analysis["impact_areas"].append("api")
                      
                      if 'models' in str(path) or 'migrations' in str(path):
                          analysis["database_changes"] = True
                          analysis["impact_areas"].append("database")
                      
                      if 'performance' in str(path) or 'optimize' in str(path):
                          analysis["performance_changes"] = True
                          analysis["impact_areas"].append("performance")
                  
                  elif path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                      analysis["files_by_type"].setdefault("frontend", []).append(str(path))
                      analysis["ui_changes"] = True
                      analysis["impact_areas"].append("ui")
                  
                  elif path.suffix in ['.md', '.rst', '.txt']:
                      analysis["documentation_changes"] = True
                      analysis["impact_areas"].append("documentation")
          
          # Output for next steps
          with open('code_analysis.json', 'w') as f:
              json.dump(analysis, f)
          
          print(f"::set-output name=impact_areas::{','.join(set(analysis['impact_areas']))}")
          print(f"::set-output name=has_api_changes::{analysis['api_changes']}")
          print(f"::set-output name=has_ui_changes::{analysis['ui_changes']}")
          EOF
      
      - name: Run Performance Analysis
        if: contains(steps.code_analysis.outputs.impact_areas, 'performance')
        run: |
          # Run benchmarks and compare
          python3 scripts/run_performance_comparison.py \
            --base-sha ${{ github.event.pull_request.base.sha }} \
            --head-sha ${{ github.event.pull_request.head.sha }} \
            --output performance_metrics.json
      
      - name: Extract Business Metrics
        run: |
          python3 << 'EOF'
          import re
          import json
          
          pr_body = '''${{ github.event.pull_request.body }}'''
          pr_title = '''${{ github.event.pull_request.title }}'''
          
          # Extract KPIs mentioned in PR
          kpis = {
              "performance": {},
              "business": {},
              "quality": {},
              "user_impact": {}
          }
          
          # Performance improvements
          perf_pattern = r'(\d+)%?\s*(faster|slower|improvement|reduction)\s*in\s*(\w+)'
          for match in re.finditer(perf_pattern, pr_body + pr_title, re.I):
              value, direction, metric = match.groups()
              kpis["performance"][metric] = {
                  "value": float(value),
                  "direction": direction,
                  "mentioned_in": "pr_description"
              }
          
          # Cost/Revenue impact
          money_pattern = r'\$(\d+\.?\d*)(k|m)?\s*(saved|revenue|cost)'
          for match in re.finditer(money_pattern, pr_body, re.I):
              amount, multiplier, impact_type = match.groups()
              value = float(amount)
              if multiplier == 'k':
                  value *= 1000
              elif multiplier == 'm':
                  value *= 1000000
              
              kpis["business"][impact_type] = value
          
          # User impact
          user_pattern = r'(\d+)%?\s*(increase|decrease|improvement)\s*in\s*(engagement|satisfaction|retention)'
          for match in re.finditer(user_pattern, pr_body, re.I):
              value, direction, metric = match.groups()
              kpis["user_impact"][metric] = {
                  "value": float(value),
                  "direction": direction
              }
          
          with open('extracted_kpis.json', 'w') as f:
              json.dump(kpis, f)
          EOF
      
      - name: Generate Achievement Stories
        id: story_generation
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python3 << 'EOF'
          import json
          import os
          from services.achievement_collector.services.story_generator import StoryGenerator
          
          # Load analysis results
          with open('code_analysis.json', 'r') as f:
              code_analysis = json.load(f)
          
          with open('extracted_kpis.json', 'r') as f:
              kpis = json.load(f)
          
          # Initialize story generator
          generator = StoryGenerator()
          
          # Generate stories based on what changed
          stories = {}
          
          # Feature story (if new functionality added)
          if code_analysis.get('api_changes') or code_analysis.get('ui_changes'):
              stories['feature'] = generator.generate_feature_story(
                  pr_data=${{ toJson(github.event.pull_request) }},
                  code_analysis=code_analysis,
                  kpis=kpis
              )
          
          # Performance story (if performance improvements)
          if code_analysis.get('performance_changes') or kpis.get('performance'):
              stories['performance'] = generator.generate_performance_story(
                  pr_data=${{ toJson(github.event.pull_request) }},
                  performance_data=kpis.get('performance', {}),
                  code_analysis=code_analysis
              )
          
          # Architecture story (if significant structural changes)
          if len(code_analysis.get('files_by_type', {})) > 5:
              stories['architecture'] = generator.generate_architecture_story(
                  pr_data=${{ toJson(github.event.pull_request) }},
                  code_analysis=code_analysis
              )
          
          # Business impact story (if KPIs mentioned)
          if kpis.get('business') or kpis.get('user_impact'):
              stories['business'] = generator.generate_business_story(
                  pr_data=${{ toJson(github.event.pull_request) }},
                  business_kpis=kpis
              )
          
          # Leadership story (if mentoring/collaboration evident)
          if len(${{ toJson(github.event.pull_request.requested_reviewers) }}) > 2:
              stories['leadership'] = generator.generate_leadership_story(
                  pr_data=${{ toJson(github.event.pull_request) }},
                  review_data=${{ toJson(github.event.pull_request.reviews) }}
              )
          
          # Save stories
          with open('generated_stories.json', 'w') as f:
              json.dump(stories, f)
          
          print(f"Generated {len(stories)} story types: {', '.join(stories.keys())}")
          EOF
      
      - name: Collect Evidence
        run: |
          # Take screenshots if UI changed
          if [ "${{ steps.code_analysis.outputs.has_ui_changes }}" = "true" ]; then
              # Run UI tests and capture screenshots
              npm run test:visual -- --screenshot
          fi
          
          # Collect performance graphs if available
          if [ -f "performance_metrics.json" ]; then
              python3 scripts/generate_performance_graphs.py
          fi
      
      - name: Store Achievement in Database
        env:
          DATABASE_URL: ${{ secrets.ACHIEVEMENT_DB_URL }}
        run: |
          python3 << 'EOF'
          import json
          from datetime import datetime
          from services.achievement_collector.db.config import get_db, engine
          from services.achievement_collector.db.models import Base
          
          # Load all collected data
          with open('code_analysis.json', 'r') as f:
              code_analysis = json.load(f)
          
          with open('extracted_kpis.json', 'r') as f:
              kpis = json.load(f)
              
          with open('generated_stories.json', 'r') as f:
              stories = json.load(f)
          
          # Create comprehensive achievement record
          achievement_data = {
              "pr_number": ${{ github.event.pull_request.number }},
              "title": "${{ github.event.pull_request.title }}",
              "description": "${{ github.event.pull_request.body }}",
              "merge_timestamp": datetime.now(),
              "author": "${{ github.event.pull_request.user.login }}",
              "reviewers": ${{ toJson(github.event.pull_request.requested_reviewers) }},
              "code_analysis": code_analysis,
              "impact_analysis": kpis,
              "stories": stories,
              "ci_metrics": {
                  "build_time": "${{ job.duration }}",
                  "workflow_run_id": "${{ github.run_id }}"
              }
          }
          
          # Store in database
          db = next(get_db())
          try:
              # Create main achievement
              achievement = create_pr_achievement(db, achievement_data)
              
              # Store detailed code changes
              for file_type, files in code_analysis.get('files_by_type', {}).items():
                  for filepath in files:
                      create_code_change_record(db, achievement.id, filepath, file_type)
              
              # Store KPI impacts
              for category, metrics in kpis.items():
                  for metric_name, value in metrics.items():
                      create_kpi_impact(db, achievement.id, category, metric_name, value)
              
              print(f"✅ Achievement {achievement.id} created with {len(stories)} stories")
              
          finally:
              db.close()
          EOF
      
      - name: Post Summary Comment
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const stories = JSON.parse(fs.readFileSync('generated_stories.json', 'utf8'));
            
            let comment = '## 🏆 Achievement Recorded!\n\n';
            comment += `This PR generated ${Object.keys(stories).length} achievement stories:\n\n`;
            
            for (const [type, story] of Object.entries(stories)) {
              comment += `### ${type.charAt(0).toUpperCase() + type.slice(1)} Story\n`;
              comment += `${story.summary}\n\n`;
            }
            
            comment += '\n📊 View full achievements at: https://your-portfolio.com/achievements';
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

## 3. Story Generator Service

```python
# services/achievement_collector/services/story_generator.py

class StoryGenerator:
    """Generate different types of achievement stories from PR data."""
    
    def __init__(self):
        self.ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def generate_feature_story(self, pr_data: Dict, code_analysis: Dict, kpis: Dict) -> Dict:
        """Generate story for feature implementation."""
        
        prompt = f"""
        Create a compelling feature implementation story:
        
        PR Title: {pr_data['title']}
        Changes: {code_analysis['impact_areas']}
        KPIs: {json.dumps(kpis)}
        
        Format as:
        - One-line impact summary
        - Technical implementation approach
        - Business value delivered
        - Skills demonstrated
        
        Make it specific and quantified.
        """
        
        response = self.ai_client.complete(prompt)
        
        return {
            "type": "feature",
            "summary": self._extract_summary(response),
            "full_story": response,
            "target_audience": ["technical", "business"],
            "skills": self._extract_skills(code_analysis),
            "impact_score": self._calculate_feature_impact(kpis)
        }
    
    def generate_performance_story(self, pr_data: Dict, performance_data: Dict, code_analysis: Dict) -> Dict:
        """Generate story for performance improvements."""
        
        if not performance_data:
            return None
            
        improvements = []
        for metric, data in performance_data.items():
            if data['direction'] in ['faster', 'improvement', 'reduction']:
                improvements.append(f"{metric}: {data['value']}% {data['direction']}")
        
        return {
            "type": "performance",
            "summary": f"Optimized system performance: {', '.join(improvements)}",
            "full_story": self._generate_performance_narrative(improvements, code_analysis),
            "target_audience": ["technical", "leadership"],
            "metrics": performance_data,
            "impact_score": self._calculate_performance_impact(performance_data)
        }
    
    def generate_business_story(self, pr_data: Dict, business_kpis: Dict) -> Dict:
        """Generate story focusing on business impact."""
        
        # Calculate total business value
        total_value = 0
        value_items = []
        
        if 'saved' in business_kpis.get('business', {}):
            saved = business_kpis['business']['saved']
            total_value += saved
            value_items.append(f"${saved:,.0f} cost savings")
            
        if 'revenue' in business_kpis.get('business', {}):
            revenue = business_kpis['business']['revenue']
            total_value += revenue
            value_items.append(f"${revenue:,.0f} revenue impact")
        
        if not value_items:
            return None
            
        return {
            "type": "business",
            "summary": f"Delivered {' and '.join(value_items)} through {pr_data['title']}",
            "full_story": self._generate_business_narrative(pr_data, business_kpis),
            "target_audience": ["business", "leadership", "executive"],
            "financial_impact": total_value,
            "roi_metrics": self._calculate_roi(pr_data, total_value)
        }
    
    def generate_architecture_story(self, pr_data: Dict, code_analysis: Dict) -> Dict:
        """Generate story for architectural improvements."""
        
        files_changed = sum(len(files) for files in code_analysis.get('files_by_type', {}).values())
        
        return {
            "type": "architecture",
            "summary": f"Refactored system architecture across {files_changed} files",
            "full_story": self._generate_architecture_narrative(pr_data, code_analysis),
            "target_audience": ["technical", "leadership"],
            "complexity_score": self._calculate_architectural_complexity(code_analysis),
            "maintainability_impact": self._assess_maintainability_improvement(code_analysis)
        }
    
    def generate_leadership_story(self, pr_data: Dict, review_data: Dict) -> Dict:
        """Generate story highlighting leadership and mentorship."""
        
        reviewer_count = len(pr_data.get('requested_reviewers', []))
        
        return {
            "type": "leadership",
            "summary": f"Led technical implementation with {reviewer_count} team members",
            "full_story": self._generate_leadership_narrative(pr_data, review_data),
            "target_audience": ["leadership", "hr"],
            "collaboration_score": self._calculate_collaboration_score(review_data),
            "mentorship_indicators": self._identify_mentorship(pr_data, review_data)
        }
```

## 4. Auto-Posting Preparation

```python
# services/achievement_collector/services/auto_poster.py

class AchievementAutoPoster:
    """Prepare achievements for auto-posting to various platforms."""
    
    async def prepare_for_posting(self, pr_achievement_id: int):
        """Prepare achievement for posting on different platforms."""
        
        achievement = await self._get_pr_achievement(pr_achievement_id)
        
        posting_data = {
            "linkedin": await self._prepare_linkedin_post(achievement),
            "twitter": await self._prepare_twitter_thread(achievement),
            "portfolio": await self._prepare_portfolio_entry(achievement),
            "blog": await self._prepare_blog_post(achievement)
        }
        
        # Update posting_metadata in database
        await self._update_posting_metadata(pr_achievement_id, posting_data)
        
        return posting_data
    
    async def _prepare_linkedin_post(self, achievement: Dict) -> Dict:
        """Prepare LinkedIn-optimized content."""
        
        # Pick the best story for LinkedIn
        best_story = self._select_best_story_for_platform(
            achievement['stories'], 
            'linkedin'
        )
        
        return {
            "content": self._format_for_linkedin(best_story),
            "hashtags": self._generate_hashtags(achievement),
            "media": achievement.get('evidence_urls', {}).get('screenshots', []),
            "ready_to_post": True
        }
```

## Benefits of This Approach

1. **Automatic Story Generation**: Every PR generates relevant stories based on actual changes
2. **Rich Data Collection**: Captures code analysis, KPIs, evidence, and metrics
3. **Future-Proof Database**: Stores everything needed for any future use case
4. **Platform-Ready**: Pre-formatted content for LinkedIn, Twitter, portfolio, etc.
5. **No Manual Work**: Fully automated from merge to story generation

## Example Output

```json
{
  "pr_number": 456,
  "title": "Optimize search performance",
  "stories": {
    "performance": {
      "summary": "Reduced search latency by 75% from 200ms to 50ms",
      "full_story": "Implemented vector-based search replacing SQL LIKE queries...",
      "metrics": {"latency": {"before": 200, "after": 50, "improvement": 75}}
    },
    "business": {
      "summary": "Delivered $15k/month cost savings through infrastructure optimization",
      "full_story": "By optimizing search performance, reduced server requirements...",
      "financial_impact": 180000
    },
    "architecture": {
      "summary": "Refactored search architecture implementing clean separation of concerns",
      "full_story": "Introduced dedicated search service with caching layer...",
      "files_impacted": 23
    }
  }
}
```

This simplified system focuses purely on extracting maximum value from each PR merge, creating a rich database of achievements ready for any future use!