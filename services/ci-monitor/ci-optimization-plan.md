# CI Workflow Optimization Plan

## Current Issues (12+ minutes):
- Building 6 Docker images every time
- Creating k3d cluster from scratch
- Installing all dependencies
- Running full e2e tests

## Proposed Solution: Multiple Workflows

### 1. **Quick CI** (2-3 minutes) - Runs on every push
```yaml
name: quick-ci
on:
  pull_request:
    branches: [main]

jobs:
  lint-and-unit:
    runs-on: ubuntu-22.04
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - name: Lint
        run: |
          pip install ruff black isort mypy
          ruff check .
          black --check .
          isort --check .
      - name: Unit tests only
        run: |
          pip install -r tests/requirements.txt
          pytest -m "not e2e" --tb=short
```

### 2. **Docker Build CI** (5-6 minutes) - Only on file changes
```yaml
name: docker-ci
on:
  pull_request:
    paths:
      - 'services/**/Dockerfile'
      - 'services/**/requirements.txt'
      - 'services/**/*.py'

jobs:
  build:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - name: Build changed services only
        run: |
          # Use GitHub API to detect which services changed
          # Only build those specific images
```

### 3. **Full E2E CI** (12 minutes) - Only on specific triggers
```yaml
name: full-ci
on:
  pull_request:
    types: [ready_for_review]  # Only when marked ready
  workflow_dispatch:  # Manual trigger
  schedule:
    - cron: '0 0 * * *'  # Nightly

jobs:
  full-test:
    # Your current workflow here
```

## Other Optimizations:

### 2. **Use Docker Registry Cache** (Save 3-4 minutes)
```yaml
- name: Login to GitHub Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}

- name: Build with registry cache
  run: |
    docker buildx build \
      --cache-from ghcr.io/${{ github.repository }}/orchestrator:cache \
      --cache-to ghcr.io/${{ github.repository }}/orchestrator:cache \
      --push \
      -t orchestrator:local .
```

### 3. **Parallelize Builds** (Save 2-3 minutes)
```yaml
jobs:
  build-matrix:
    strategy:
      matrix:
        service: [orchestrator, celery_worker, persona_runtime, fake_threads, viral_engine, revenue]
    steps:
      - name: Build ${{ matrix.service }}
        run: |
          docker buildx build \
            -f services/${{ matrix.service }}/Dockerfile \
            -t ${{ matrix.service }}:local .
```

### 4. **Skip Unchanged Services**
```yaml
- name: Check if service changed
  id: changes
  uses: dorny/paths-filter@v2
  with:
    filters: |
      orchestrator:
        - 'services/orchestrator/**'
      celery_worker:
        - 'services/celery_worker/**'

- name: Build orchestrator
  if: steps.changes.outputs.orchestrator == 'true'
  run: docker build services/orchestrator
```

### 5. **Use Pre-built Test Cluster**
Instead of creating k3d cluster every time:
```yaml
- name: Use k3d-action with image preloading
  uses: AbsaOSS/k3d-action@v2
  with:
    cluster-name: dev
    args: >-
      --image-volume /tmp/k3d-images:/images
      --k3s-arg "--disable=traefik@server:0"
```

### 6. **Smart Test Selection**
```yaml
- name: Run relevant tests only
  run: |
    # Detect which services changed
    CHANGED_SERVICES=$(git diff --name-only origin/main...HEAD | grep "^services/" | cut -d/ -f2 | sort -u)

    # Run tests only for changed services
    for svc in $CHANGED_SERVICES; do
      pytest tests/unit/test_${svc}.py
    done
```

## Recommended Implementation Order:

1. **Week 1**: Implement Quick CI (immediate 10-minute savings)
2. **Week 2**: Add Docker registry caching
3. **Week 3**: Implement smart test selection
4. **Week 4**: Fine-tune based on metrics

## Expected Results:
- **Every push**: 2-3 minutes (lint + unit tests)
- **Code changes**: 5-6 minutes (rebuild only changed services)
- **Ready for review**: 12 minutes (full e2e)
- **90% of pushes**: Under 3 minutes

## GitHub Settings to Add:
1. Require "quick-ci" to pass
2. Require "full-ci" only for merge
3. Allow developers to manually trigger full-ci
