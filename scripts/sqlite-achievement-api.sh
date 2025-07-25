#!/bin/bash
# Run achievement collector with SQLite backend

# Set SQLite mode
export DATABASE_URL="sqlite:///$HOME/.threads-agent/achievements/achievements.db"
export USE_SQLITE=true

# Create directory if needed
mkdir -p ~/.threads-agent/achievements

# Initialize database
python -c "
import sys
sys.path.append('.')
from services.achievement_collector.db.sqlite_config import init_sqlite_db
init_sqlite_db()
"

# Store the CI achievement first
echo "📝 Storing CI achievement..."
python scripts/achievement-local-store.py

# Start the API server
echo "🚀 Starting Achievement Collector API with SQLite..."
cd services/achievement_collector
uvicorn main:app --host 0.0.0.0 --port 8084 --reload