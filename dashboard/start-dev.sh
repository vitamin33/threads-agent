#!/bin/bash

echo "🚀 Starting Threads-Agent Streamlit Dashboard"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run setup script first."
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start Streamlit
echo "✅ Dashboard starting at http://localhost:8501"
echo "📊 Main dashboard: http://localhost:8501"
echo "🔍 Health check: http://localhost:8501/_stcore/health"
echo ""
echo "Press Ctrl+C to stop"

streamlit run app.py
