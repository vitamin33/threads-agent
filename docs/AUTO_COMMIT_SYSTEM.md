# Auto-Commit System for Working States

## Overview

The auto-commit system helps maintain a stable, working codebase by automatically creating checkpoint commits when tests pass. This ensures you always have a known-good state to revert to.

## Features

1. **Test-Driven Commits**: Only creates commits when tests pass (with option for WIP commits)
2. **Pre-Push Protection**: Prevents pushing broken code to remote
3. **Scheduled Checkpoints**: Automatic commits every 30 minutes in safe-dev mode
4. **GitHub Actions Integration**: Auto-checkpoints on successful CI runs

## Usage

### Manual Checkpoint
```bash
# Create a checkpoint commit (runs tests first)
just checkpoint

# Create checkpoint and push to remote
just checkpoint-push

# Create checkpoint with custom message
just checkpoint "feat: added new feature"
```

### Safe Development Mode
```bash
# Start safe development mode (auto-commits every 30 minutes)
just safe-dev
```

### Direct Script Usage
```bash
# Run auto-commit script directly
./scripts/auto-commit.sh

# Auto-commit and push if tests pass
./scripts/auto-commit.sh --push
```

### Skip Tests on Push (Emergency)
```bash
# Force push without running tests
SKIP_TESTS=1 git push
```

## How It Works

1. **Pre-Push Hook**: Runs `just check` before allowing push
2. **Auto-Commit Script**: 
   - Checks for uncommitted changes
   - Runs test suite
   - Creates commit with test status
   - Optionally pushes to remote

3. **Commit Format**:
   ```
   [auto-commit] ✅ Working state - all tests passing
   
   Branch: feature/new-feature
   Timestamp: 2024-01-15 14:30:00
   Test Status: PASSED
   ```

## Configuration

### Enable/Disable Auto-Commit
```bash
# Enable auto-commit system
just auto-commit-enable

# Disable auto-commit system
just auto-commit-disable
```

### GitHub Actions

The system includes a GitHub Actions workflow that:
- Runs after successful CI builds
- Creates checkpoints every 2 hours during work hours
- Only commits if there are actual changes

## Best Practices

1. **Use Checkpoints Before Risky Changes**: Create a checkpoint before refactoring or major changes
2. **Review Auto-Commits**: Periodically squash auto-commits into meaningful commits
3. **Keep Tests Fast**: Auto-commit works best with fast test suites
4. **Use Descriptive Messages**: When manually creating checkpoints, add context

## Troubleshooting

### Tests Failing But Need to Push
```bash
# Skip tests temporarily (use sparingly!)
SKIP_TESTS=1 git push

# Or create WIP commit
git add . && git commit -m "WIP: debugging test failures"
```

### Auto-Commit Not Working
```bash
# Check if script is executable
chmod +x scripts/auto-commit.sh

# Check git hooks
ls -la .git/hooks/

# Run with debug output
bash -x scripts/auto-commit.sh
```

## Integration with Development Workflow

The auto-commit system integrates seamlessly with the existing workflow:

```bash
# Morning: Start work with clean state
just work-day

# During development: Regular checkpoints
just checkpoint "implemented user auth"

# Before lunch/breaks: Quick checkpoint
just checkpoint

# End of day: Final checkpoint and analysis
just checkpoint-push
just end-day
```

This ensures you never lose work and always have a trail of working states!