# GitHub Actions Achievement Tracker Setup Guide

## Overview

The Achievement Tracker is a GitHub Actions workflow that automatically creates achievements in your PostgreSQL database whenever a PR is merged. It extracts comprehensive metrics from PRs and stores them for portfolio generation, career tracking, and professional growth analytics.

## Features

- **Automatic Tracking**: Triggers on every PR merge
- **Comprehensive Metrics**: Extracts 50+ data points from PRs
- **Business Impact Analysis**: Identifies cost savings, user impact, and revenue implications
- **Skill Extraction**: Automatically identifies technologies and skills demonstrated
- **Metadata Storage**: Captures GitHub run URLs, PR links, and collection metadata

## Prerequisites

1. **PostgreSQL Database**: Hosted database (e.g., Supabase, AWS RDS)
2. **GitHub Repository**: With Actions enabled
3. **Secrets Configuration**: Database URL stored in repository secrets

## Setup Instructions

### 1. Database Setup

First, ensure you have a PostgreSQL database with the achievement collector schema:

```bash
# Set your database URL
export ACHIEVEMENT_DB_URL="postgresql://user:password@host:port/database"

# Initialize the schema (run from the achievement_collector directory)
cd services/achievement_collector
python3 -c "
from db.config import engine
from db.models import Base
Base.metadata.create_all(bind=engine)
"
```

### 2. GitHub Secrets Configuration

Add the following secret to your repository:
- Go to Settings → Secrets and variables → Actions
- Add `ACHIEVEMENT_DB_URL` with your PostgreSQL connection string

### 3. Workflow File

The workflow is already set up at `.github/workflows/achievement-tracker.yml`. Key features:

```yaml
name: Achievement Tracker

on:
  pull_request:
    types: [closed]

jobs:
  track-achievement:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
```

## How It Works

### 1. PR Metrics Collection
The workflow extracts:
- PR title, body, and metadata
- Code changes (additions, deletions, files)
- Review information (reviewers, comments)
- Labels and merge time

### 2. Business Metrics Extraction
Searches PR descriptions for:
- Performance improvements
- Cost reductions
- User impact
- Revenue implications
- Security enhancements

### 3. Impact Score Calculation
Calculates a 0-100 score based on:
- **Base score**: 50 points
- **Size bonus**: +5 to +20 points for code volume
- **Review bonus**: +5 to +10 points for peer reviews
- **Business impact**: +5 to +15 points per impact type
- **Planning context**: +5 points for linked epics/issues

### 4. Achievement Storage
Creates an achievement record with:
- **Title**: "Shipped: [PR Title]"
- **Description**: PR body + delivery details
- **Category**: Determined from PR content (feature, bugfix, etc.)
- **Skills**: Extracted from changed files and technologies
- **Metrics**: Comprehensive PR and business metrics
- **Metadata**: GitHub run URL, PR URL, collector info

## Metrics Captured

### PR Metrics
- `pr_number`: Pull request number
- `title`: PR title
- `body`: Full PR description
- `additions`/`deletions`: Lines changed
- `changed_files`: Number of files modified
- `commits`: Number of commits
- `review_count`: Number of reviews
- `merge_time_hours`: Time from creation to merge

### Business Metrics
- `has_performance_improvement`: Boolean flag
- `has_cost_reduction`: Boolean flag
- `has_user_impact`: Boolean flag
- `has_revenue_impact`: Boolean flag
- `has_security_improvement`: Boolean flag
- KPI values extracted from PR body (if mentioned)

### Planning Metrics
- `linear_issues`: Linked Linear issue IDs
- `epic`: Associated epic name
- `sprint`: Sprint number
- `has_planning_context`: Boolean flag

## Data Structure

Achievements are stored with the following structure:

```json
{
  "title": "Shipped: Optimize API performance",
  "category": "optimization",
  "description": "Implemented caching layer...",
  "impact_score": 85,
  "complexity_score": 70,
  "source_type": "github_pr",
  "source_id": "PR-123",
  "skills_demonstrated": ["Python", "Redis", "Performance Optimization"],
  "metrics_after": {
    "pr_number": 123,
    "additions": 245,
    "deletions": 89,
    "business": {
      "has_performance_improvement": true,
      "engagement_rate": "6.5"
    },
    "performance": {
      "test_execution_time": "120s",
      "code_coverage": "85%"
    }
  },
  "metadata_json": {
    "github_run_url": "https://github.com/org/repo/actions/runs/12345",
    "pr_url": "https://github.com/org/repo/pull/123",
    "collected_by": "github-actions"
  }
}
```

## Best Practices

### 1. PR Descriptions
To maximize the value of automatic collection:

**Include Metrics**:
```markdown
## Changes
- Reduced API latency by 40% (from 200ms to 120ms)
- Affects 10,000 daily active users
- Saves approximately $5,000/month in server costs

## Implementation
- Added Redis caching layer
- Optimized database queries
- Implemented connection pooling
```

**Use Labels**:
- `performance`: For optimization PRs
- `feature`: For new functionality
- `bugfix`: For bug fixes
- `security`: For security improvements

### 2. Linking Context
- Reference Linear issues: "Fixes ABC-123"
- Mention epics: "Epic: Performance Q1"
- Include sprint info: "Sprint 15"

## Troubleshooting

### Achievement Not Created
1. Check if PR was merged (not just closed)
2. Verify workflow ran successfully in Actions tab
3. Check database connection in workflow logs

### Empty Business Value
- Business value requires specific numeric values in PR description
- Example: "Saves $15,000 annually" or "Improves performance by 40%"
- Boolean flags alone don't generate business value text

### Missing Metadata
- Ensure you have the latest workflow version
- The metadata fix adds GitHub run URLs and PR links

## Future Enhancements

### AI-Powered Analysis (Planned)
- Extract business value from unstructured text
- Generate professional summaries
- Identify hidden impact and skills

### Multi-Platform Publishing (Planned)
- Auto-post to LinkedIn
- Update GitHub profile README
- Generate portfolio website content

## API Access

Query achievements programmatically:

```python
# Get recent PR achievements
GET /achievements?source_type=github_pr&sort_by=completed_at&order=desc

# Get specific PR achievement
GET /achievements?source_id=PR-123
```

## Support

For issues or questions:
1. Check workflow logs in GitHub Actions
2. Verify database connectivity
3. Ensure PR has sufficient content for meaningful achievement

---

*Last Updated: January 2025*