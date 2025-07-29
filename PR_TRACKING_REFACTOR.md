# PR-Based Achievement Tracking Refactor

## Summary of Changes

We've refactored the achievement tracking system from commit-based to PR-based tracking. This provides better quality achievements that represent complete features rather than individual commits.

## Key Changes

### 1. New GitHub PR Tracker
- **File**: `services/achievement_collector/services/github_pr_tracker.py`
- Tracks merged PRs instead of individual commits
- Uses GitHub CLI (`gh`) for API access
- Analyzes PR metrics: files changed, additions/deletions, reviews, labels
- Creates achievements only for significant PRs (50+ changes or important labels)

### 2. Updated Auto Tracker
- **File**: `services/achievement_collector/services/auto_tracker.py`
- Now imports and uses `GitHubPRTracker` instead of `GitCommitTracker`
- Environment variable changed from `ENABLE_GIT_TRACKING` to `ENABLE_GITHUB_TRACKING`

### 3. New Tests
- **File**: `services/achievement_collector/tests/test_github_pr_tracker.py`
- Comprehensive test suite for PR tracking functionality
- Tests for significance detection, skill extraction, scoring algorithms

### 4. Updated Scripts
- **start-achievement-tracker.py**: Now configured for PR tracking
- **test-achievement-integration.py**: Updated to test PR tracking
- **demo-github-pr-tracker.py**: New demo script for PR functionality
- **migrate-to-pr-tracking.py**: Migration guide for users

### 5. Webhook Support
- Existing webhook infrastructure in `api/routes/webhooks.py` supports PR events
- Can receive real-time GitHub webhook notifications for merged PRs

## Benefits of PR-Based Tracking

1. **Quality over Quantity**: One achievement per feature, not per commit
2. **Better Metrics**: 
   - Review participation shows collaboration
   - PR discussions show communication skills
   - Multiple commits show iterative development
3. **Richer Context**: PR descriptions explain the "why"
4. **Professional Portfolio**: PRs better represent actual work delivered

## Usage

### Basic Usage (Polling)
```bash
# Start the tracker (polls GitHub every 5 minutes)
python3 scripts/start-achievement-tracker.py
```

### With GitHub CLI
```bash
# Install and authenticate
brew install gh
gh auth login

# The tracker will use gh to fetch PR data
python3 scripts/start-achievement-tracker.py
```

### With Webhooks (Real-time)
1. Add webhook to your GitHub repo settings
2. Point to: `https://your-domain.com/webhooks/github`
3. Select events: Pull requests
4. Set `GITHUB_WEBHOOK_SECRET` environment variable

## Migration from Commit Tracking

Run the migration guide:
```bash
python3 scripts/migrate-to-pr-tracking.py
```

This will walk you through:
- Updating environment variables
- Installing GitHub CLI
- Removing old git hooks
- Testing the new system

## Environment Variables

```bash
# Old (commit-based)
ENABLE_GIT_TRACKING=true
MIN_LINES_FOR_ACHIEVEMENT=50

# New (PR-based)
ENABLE_GITHUB_TRACKING=true
MIN_PR_CHANGES_FOR_ACHIEVEMENT=50
PR_CHECK_INTERVAL=300
GITHUB_TOKEN=your_token  # Optional
```

## What Happens to Existing Achievements?

- Existing commit-based achievements remain in your database
- They will still appear in your portfolio
- New achievements will be created from PRs only
- No data loss or migration needed

## Next Steps

1. Test with: `python3 scripts/demo-github-pr-tracker.py`
2. Start tracking: `python3 scripts/start-achievement-tracker.py`
3. Optional: Set up GitHub webhooks for real-time tracking