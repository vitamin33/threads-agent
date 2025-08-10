# GitHub Actions Workflows

This directory contains the CI/CD workflows for the threads-agent project.

## Active Workflows

### Core CI/CD
- **dev-ci.yml** - Main CI workflow that runs on PRs to main branch
  - Builds Docker images
  - Deploys to k3d cluster using Helm
  - Runs e2e tests
  
- **quick-ci.yml** - Fast unit test runner
  - Runs Python unit tests
  - Linting and type checking
  - Runs on all PRs for quick feedback

- **docker-ci.yml** - Docker build validation
  - Triggered on Dockerfile or requirements.txt changes
  - Ensures all services build correctly

### Automation
- **achievement-tracker.yml** - Tracks PR achievements
  - Runs when PRs are closed
  - Records achievements and metrics

- **linear-auto-done.yml** - Linear issue automation
  - Moves Linear issues to "Done" when PRs are merged
  - Triggered on PR close

- **pr-value-analysis.yml** - PR value assessment
  - Analyzes PR business value and technical impact
  - Runs on PR open/edit and merge

## Archived Workflows
Unused or experimental workflows are stored in the `archived/` directory.