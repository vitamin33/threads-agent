#!/bin/bash
set -e

echo "Setting up RAG Pipeline environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Add parent directory to PYTHONPATH for imports
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../.."

# Run tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v --tb=short

echo "Tests completed!"