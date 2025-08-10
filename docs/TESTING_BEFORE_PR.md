# 🧪 Testing Before Creating PRs - Best Practices

## Why Tests Failed in CI but Not Locally

The `psutil` error that failed CI was missed locally because:

1. **Missing Dependency**: `psutil` wasn't in `tests/requirements.txt`
2. **No Pre-PR Test Execution**: Our workflow didn't enforce running tests before push
3. **E2E Tests Skipped Locally**: Developers often skip e2e tests due to time/complexity

## Recommended Workflow to Prevent This

### 1. **Use Pre-PR Checks Script** (Recommended)
```bash
# Run this before every PR
./scripts/pre-pr-checks.sh

# Or use Make
make pre-pr

# Or use Just
just pre-pr
```

### 2. **Set Up Your Local Environment Properly**
```bash
# Always install ALL dependencies
pip install -r tests/requirements.txt
pip install -r services/*/requirements.txt

# Or use our helper
just install-deps
```

### 3. **Run Tests in Stages**

#### Stage 1: Quick Checks (< 1 minute)
```bash
# Before every commit
just lint          # Code style
just type-check    # Type checking
```

#### Stage 2: Unit Tests (2-3 minutes)
```bash
# Before pushing
just unit          # Fast unit tests
# or
pytest -m "not e2e" -q
```

#### Stage 3: Integration Tests (5-10 minutes)
```bash
# Before creating PR
just test          # Full test suite
# or for e2e only
just e2e
```

### 4. **Use Git Hooks** (Automated)
```bash
# Install enhanced hooks
./scripts/install-git-hooks.sh

# Enable test running on push
export RUN_TESTS_BEFORE_PUSH=1
```

### 5. **CI-Like Local Testing**
```bash
# Simulate exactly what CI does
just ci-local

# Or manually
docker build -t test-env .
docker run test-env pytest
```

## Quick Reference Checklist

Before creating a PR, run:

```bash
# Option 1: Just command (easiest)
just check

# Option 2: Manual steps
ruff check .                              # Lint
mypy services/                            # Type check
pytest -m "not e2e" -q                   # Unit tests
grep -r "print(" services/                # Debug prints
pip install -r tests/requirements.txt     # Dependencies

# Option 3: Full validation (requires k3d)
just dev-start                            # Start cluster
just e2e                                  # Run e2e tests
```

## Preventing Dependency Issues

1. **Always sync dependencies**:
   ```bash
   # When pulling new code
   git pull
   pip install -r tests/requirements.txt
   ```

2. **Check for missing imports**:
   ```bash
   # Quick check
   python -c "import psutil, httpx, pytest, qdrant_client"
   ```

3. **Use virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r tests/requirements.txt
   ```

## GitHub Actions Integration

To make CI match local:

1. **Same Python version**: Use Python 3.12 locally
2. **Same dependencies**: Keep requirements.txt updated
3. **Same test commands**: Use same pytest flags

## Summary

The `psutil` error could have been caught by:
1. ✅ Running `pip install -r tests/requirements.txt` 
2. ✅ Running `pytest -m "not e2e"` before push
3. ✅ Using `just pre-pr` command
4. ✅ Having better git hooks

Going forward, make it a habit to run `just check` or `make pre-pr` before creating any PR!