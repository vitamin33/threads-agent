# CI Optimization Guide

## Overview

This guide documents the CI workflow optimizations implemented to reduce the 12+ minute CI runtime to under 5 minutes for most cases.

## 3-Tier CI System

### 1. Quick CI (quick-ci.yml) - 2-3 minutes
- **Triggers**: Every push to PR branches
- **Purpose**: Fast feedback on code quality
- **What it runs**:
  - Linting (ruff, black, isort)
  - Unit tests only (no e2e)
  - Type checking (mypy)
- **Parallel execution**: Tests run per service in matrix

### 2. Docker CI (docker-ci.yml) - 5-6 minutes
- **Triggers**: Only when Docker-related files change
- **Purpose**: Build and push images to GitHub Container Registry
- **Features**:
  - Smart change detection with dorny/paths-filter
  - Only builds changed services
  - Pushes to GHCR for caching
  - Uses layer caching for faster builds

### 3. Full CI (dev-ci.yml) - 5-8 minutes (was 12+ minutes)
- **Triggers**:
  - Pull requests to main
  - Manual workflow dispatch
- **Optimizations**:
  - Pulls pre-built images from GHCR instead of building
  - Falls back to local build only if image not found
  - Workflow dispatch option to force rebuild

## Key Improvements

### Before (12+ minutes)
1. Build all 6 service images from scratch
2. Set up BuildKit and manage local cache
3. Wait for all builds to complete sequentially
4. Import to k3d
5. Run tests

### After (5-8 minutes)
1. Login to GHCR
2. Pull pre-built images (seconds per image)
3. Only build if image missing
4. Import to k3d
5. Run tests

## Branch Protection Rules

Update your branch protection rules to require these checks:

### Required Checks
- `quick-ci / py3.12 • quick` - Must pass on every push
- `docker-ci / docker-summary` - Must pass if Docker files changed
- `dev-ci / py3.12 • k3d` - Must pass for merge

### Recommended Settings
```yaml
- Require branches to be up to date before merging: ✓
- Require status checks to pass before merging: ✓
  - quick-ci / py3.12 • quick
  - dev-ci / py3.12 • k3d
- Require conversation resolution before merging: ✓
- Require linear history: ✓
```

## Manual CI Runs

You can manually trigger the full CI with optional force rebuild:

1. Go to Actions → dev-ci workflow
2. Click "Run workflow"
3. Select options:
   - Branch: Choose branch to test
   - Force build: Set to 'true' to rebuild all images

## Cost Savings

- **Developer Time**: ~7 minutes saved per CI run
- **GitHub Actions**: Reduced compute minutes by ~60%
- **Storage**: GHCR provides 500MB free storage per repo

## Troubleshooting

### Images not found in GHCR
- Check if docker-ci workflow ran for your PR
- Ensure Docker files were actually changed
- Verify GHCR permissions are configured

### Force rebuild needed
- Use workflow dispatch with force_build=true
- Or make a small change to trigger docker-ci

### Quick CI failing
- Run `just lint` locally before pushing
- Ensure `just unit` passes locally
