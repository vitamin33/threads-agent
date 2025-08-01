#!/bin/bash
# Start the Dashboard API server

cd "$(dirname "$0")"

echo "🚀 Starting Real-Time Variant Performance Dashboard"
echo "=================================================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment not activated!"
    echo "Run: source ../../venv/bin/activate"
    exit 1
fi

# Check if required packages are installed
python -c "import uvicorn, fastapi" 2>/dev/null || {
    echo "❌ Missing dependencies. Install with:"
    echo "pip install -r requirements.txt"
    exit 1
}

echo "✅ Dependencies OK"
echo "✅ Starting server on http://localhost:8081"
echo ""
echo "Available endpoints:"
echo "- GET  / - Health check"
echo "- GET  /api/metrics/{persona_id} - Dashboard metrics"
echo "- GET  /api/variants/{persona_id}/active - Active variants"
echo "- WS   /dashboard/ws/{persona_id} - WebSocket updates"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================================="

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8081 --reload