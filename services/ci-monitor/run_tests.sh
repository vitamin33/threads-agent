#!/bin/bash
set -e

PROJECT_ROOT="/Users/vitaliiserbyn/development/threads-agent"
cd "$PROJECT_ROOT"

# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT"
export OPENAI_API_KEY="test"

# Run unit tests (excluding achievement_collector for now)
pytest -q -m "not e2e" -n auto --ignore=services/achievement_collector