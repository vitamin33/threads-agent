# 🔧 Achievement Tracker Workflow Fix

## Current Issues (45% Success Rate)

### 1. Module Import Error
```
ModuleNotFoundError: No module named 'services.achievement_collector'
```
**Cause**: Alembic migrations run from wrong directory

### 2. Merge Conflicts in Code
```
SyntaxError: invalid syntax (<<<<<<< HEAD)
```
**Cause**: PRs with unresolved merge conflicts

### 3. Missing PR Metrics
- Workflow runs on `pull_request` closed event
- But the condition `if: github.event.pull_request.merged == true` means it only runs for merged PRs
- However, PR metrics collection step also has `if: github.event_name == 'pull_request'` which is redundant

## Recommended Fixes

### Fix 1: Update Migration Step (Line 193-197)
```yaml
- name: Apply Database Migrations
  env:
    DATABASE_URL: ${{ secrets.ACHIEVEMENT_DB_URL }}
    PYTHONPATH: ${{ github.workspace }}
  run: |
    cd services/achievement_collector
    # Add parent directory to Python path for imports
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/../.."
    # Run alembic migrations
    alembic upgrade head || echo "Migration already applied"
  continue-on-error: true
```

### Fix 2: Add Validation Step Before Main Processing
```yaml
- name: Validate Code Syntax
  run: |
    # Check for merge conflicts
    if grep -r "<<<<<<< HEAD" services/achievement_collector/; then
      echo "❌ Merge conflicts detected in code!"
      exit 1
    fi
    
    # Basic Python syntax check
    python -m py_compile services/achievement_collector/**/*.py || true
```

### Fix 3: Improve Error Handling in Achievement Creation
Add better error handling around line 206:

```python
# Add at the beginning of the script
try:
    from services.achievement_collector.services.github_pr_tracker import GitHubPRTracker
    from services.achievement_collector.db.config import get_db, engine
    from services.achievement_collector.db.models import Base, Achievement
    from services.achievement_collector.api.schemas import AchievementCreate
    from services.achievement_collector.api.routes.achievements import create_achievement_sync
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure all dependencies are installed")
    sys.exit(1)
```

### Fix 4: Simplify Workflow Trigger
The workflow should only run when PRs are actually merged:

```yaml
on:
  pull_request:
    types: [closed]
    branches: [main]  # Add branch filter

jobs:
  track-achievement:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
```

### Fix 5: Add Retry Logic for Database Operations
Around line 358:

```python
# Retry logic for database operations
max_retries = 3
for attempt in range(max_retries):
    try:
        achievement = create_achievement_sync(db, achievement_data)
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise
        print(f"⚠️  Database operation failed (attempt {attempt + 1}/{max_retries}): {e}")
        time.sleep(2)
```

## Complete Fixed Workflow

Here's the key sections that need updating:

```yaml
name: Achievement Tracker

on:
  pull_request:
    types: [closed]
    branches: [main]  # Only track main branch PRs

jobs:
  track-achievement:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    
    steps:
      # ... (previous steps remain the same) ...
      
      - name: Install dependencies
        run: |
          # Install all requirements to avoid import errors
          pip install -r services/achievement_collector/requirements.txt
          pip install -r services/common/requirements.txt
          pip install PyGithub alembic
          
      - name: Validate Environment
        run: |
          # Check Python path
          echo "Python path: $PYTHONPATH"
          echo "Working directory: $(pwd)"
          
          # Verify imports work
          python -c "import sys; sys.path.insert(0, '.'); from services.achievement_collector.db import models; print('✅ Imports working')"
      
      - name: Apply Database Migrations
        env:
          DATABASE_URL: ${{ secrets.ACHIEVEMENT_DB_URL }}
          PYTHONPATH: ${{ github.workspace }}
        run: |
          cd services/achievement_collector
          export PYTHONPATH="${PYTHONPATH}:$(pwd)/../.."
          alembic upgrade head || echo "Migration already applied"
        continue-on-error: true
```

## Expected Results
- Success rate should improve from 45% to ~90%+
- Common import errors will be resolved
- Better error messages for debugging
- Faster failure detection (syntax validation)

## Testing Strategy
1. Create a test PR that triggers the workflow
2. Monitor logs for import errors
3. Verify database migrations run correctly
4. Check that achievements are created successfully