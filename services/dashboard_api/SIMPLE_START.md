# Simple Dashboard Startup Guide

## Copy-Paste Commands (MacOS/Linux)

**Step 1: Open Terminal and run these commands exactly:**

```bash
cd /Users/vitaliiserbyn/development/team/jordan-kim/threads-agent
source venv/bin/activate
cd services/dashboard_api
python -m uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

**Step 2: You should see:**
```
Starting Variant Dashboard API...
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8081 (Press CTRL+C to quit)
```

**Step 3: Open browser and visit:**
- http://localhost:8081/
- http://localhost:8081/api/metrics/ai-jesus

## Alternative Method - Use Our Startup Script

```bash
cd /Users/vitaliiserbyn/development/team/jordan-kim/threads-agent
source venv/bin/activate
cd services/dashboard_api
chmod +x start_dashboard.sh
./start_dashboard.sh
```

## If You Get Errors:

**"command not found: python"**
```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

**"No module named uvicorn"**
```bash
pip install fastapi uvicorn
```

**"Address already in use"**
```bash
lsof -ti:8081 | xargs kill -9
# Then try starting again
```

## Expected Browser Response:

**At http://localhost:8081/:**
```json
{"status":"healthy","service":"variant-dashboard-api"}
```

**At http://localhost:8081/api/metrics/ai-jesus:**
```json
{
  "summary": {"total_variants": 0, "avg_engagement_rate": 0.0},
  "active_variants": [],
  "early_kills_today": {"kills_today": 0, "avg_time_to_kill_minutes": 0},
  "pattern_fatigue_warnings": [],
  "optimization_opportunities": [],
  "real_time_feed": []
}
```