# Achievement Auto-Collection System

## Overview
The Achievement Auto-Collection system automatically tracks and creates achievements from your development work across multiple sources:
- GitHub Pull Requests (merged PRs with significant changes)
- Linear issues and epics
- MLflow experiments (pending E4.5 implementation)

## Why PR-Based Tracking?

We track PRs instead of individual commits because:
- **Quality over Quantity**: One achievement per feature, not per commit
- **Better Metrics**: Review participation, discussions, iterations  
- **Richer Context**: PR descriptions provide the "why" behind changes
- **Team Collaboration**: Shows code review and collaboration skills

## Architecture

### Core Components

1. **GitHub PR Tracker** (`services/achievement_collector/services/github_pr_tracker.py`)
   - Monitors merged PRs for significant changes
   - Creates achievements based on PR size, reviews, and labels
   - Extracts skills from files changed and PR metadata
   
2. **Linear Tracker** (`services/achievement_collector/services/linear_tracker.py`)
   - Tracks completed Linear issues and epics
   - Creates achievements with priority-based impact scores
   - Extracts skills from labels and descriptions
   
3. **Auto Tracker Coordinator** (`services/achievement_collector/services/auto_tracker.py`)
   - Manages all tracking services
   - Handles graceful startup/shutdown
   - Configurable via environment variables

### Data Flow
```
GitHub PRs → PR Tracker ↘
                         → Achievement Database → Export/Publishing
Linear Issues → Linear Tracker ↗
```

## Setup and Configuration

### Environment Variables
```bash
# GitHub PR Tracking
GIT_REPO_PATH=.                    # Repository to monitor
MIN_PR_CHANGES_FOR_ACHIEVEMENT=50  # Minimum changes for PR achievement
ENABLE_GITHUB_TRACKING=true        # Enable/disable GitHub PR tracking
PR_CHECK_INTERVAL=300              # Check interval in seconds (5 min)
GITHUB_TOKEN=your_token            # Optional: GitHub personal access token

# Linear Tracking  
LINEAR_API_KEY=your_key            # Linear API key (uses MCP in production)
LINEAR_CHECK_INTERVAL=3600         # Check interval in seconds

# Database
DATABASE_URL=postgresql://...       # Achievement storage
```

### Git Hook Setup
To track commits in real-time, add to `.git/hooks/post-commit`:
```bash
#!/bin/bash
python3 scripts/track-commit-achievement.py
```

## Usage

### Start Auto-Tracker
```bash
# Development/testing
python3 scripts/start-achievement-tracker.py

# Production (with proper environment)
python3 -m services.achievement_collector.services.auto_tracker
```

### Test Individual Components
```bash
# Test Linear tracker with mock data
python3 scripts/test-linear-tracker.py

# Test simple achievement functionality
python3 scripts/test-achievement-simple.py
```

## Achievement Creation Logic

### Git Commits
Commits are considered significant if they:
- Match conventional commit patterns (feat, fix, perf, etc.)
- Change more than MIN_LINES_FOR_ACHIEVEMENT lines
- Contain keywords like "implement", "build", "deploy"

### Linear Issues
Issues create achievements with:
- Category based on labels (feature, bugfix, performance, etc.)
- Impact score based on priority (Urgent: 90, High: 75, Medium: 60)
- Complexity score based on estimate points
- Skills extracted from labels and description

### Scoring System
- **Impact Score**: 0-100 based on priority and scope
- **Complexity Score**: 0-100 based on effort and technical depth
- **Portfolio Ready**: Achievements with impact >= 70

## Next Steps

### Pending Implementation
1. **LinkedIn Auto-Publisher** (Task 3)
   - OAuth integration
   - Post formatting
   - Scheduling logic

2. **GitHub Profile Updater** (Task 4)
   - README generation
   - Stats aggregation
   - Auto-commit

3. **Celery Scheduling** (Task 5)
   - Periodic publishing
   - Rate limiting
   - Retry logic

### MLflow Integration (After E4.5)
When MLOps Foundation epic is complete:
```python
# In auto_tracker.py
if os.getenv("MLFLOW_TRACKING_URI"):
    tasks.append(asyncio.create_task(self.mlflow_tracker.track_experiments()))
```

## API Integration

### Internal Achievement Creation
```python
from services.achievement_collector.api.schemas import AchievementCreate
from services.achievement_collector.api.routes.achievements import create_achievement_sync

achievement = AchievementCreate(
    title="Completed: Feature Implementation",
    category="feature",
    description="Implemented new OAuth flow",
    source_type="git",
    source_id="commit_hash",
    impact_score=75.0,
    complexity_score=80.0,
    skills_demonstrated=["Python", "OAuth", "Security"]
)

db = next(get_db())
result = create_achievement_sync(db, achievement)
```

## Monitoring

The system logs all activities:
- `✅` Successful achievement creation
- `ℹ️` Skipped non-significant items  
- `❌` Errors with full traceback
- `🔍` Processing status updates

## Testing

Run tests with:
```bash
# Unit tests
pytest services/achievement_collector/tests/

# E2E tests (requires database)
pytest services/achievement_collector/tests/ -m e2e
```

## GitHub Actions Integration

The project includes a GitHub Actions workflow (`.github/workflows/achievement-tracker.yml`) that automatically creates achievements when PRs are merged. See [GitHub Actions Setup Guide](./GITHUB_ACTIONS_SETUP.md) for configuration details.

### Key Features:
- Triggers only on PR merge (not on push or close)
- Extracts business metrics from PR descriptions
- Calculates impact scores based on PR characteristics
- Stores comprehensive metadata including GitHub run URLs

### Common Issues:
- **Empty business_value**: Include specific numbers in PR descriptions (e.g., "$15,000 saved")
- **Missing metadata**: Update to latest workflow version with metadata fix
- **No achievement created**: Verify PR was merged (not just closed)