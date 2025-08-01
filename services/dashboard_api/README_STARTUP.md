# How to Start the Dashboard API

## Quick Start

1. **Activate virtual environment:**
   ```bash
   cd /Users/vitaliiserbyn/development/team/jordan-kim/threads-agent
   source venv/bin/activate
   ```

2. **Start the dashboard:**
   ```bash
   cd services/dashboard_api
   ./start_dashboard.sh
   ```

3. **Test the dashboard:**
   Open another terminal and run:
   ```bash
   cd services/dashboard_api
   python test_client.py
   ```

## Manual Commands

If the script doesn't work, run these commands manually:

```bash
# 1. Navigate to project
cd /Users/vitaliiserbyn/development/team/jordan-kim/threads-agent

# 2. Activate virtual environment
source venv/bin/activate

# 3. Go to dashboard API
cd services/dashboard_api

# 4. Start server
uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

## Accessing the Dashboard

Once the server is running, you can access:

- **Health Check:** http://localhost:8081/
- **Metrics API:** http://localhost:8081/api/metrics/ai-jesus
- **Active Variants:** http://localhost:8081/api/variants/ai-jesus/active
- **WebSocket:** ws://localhost:8081/dashboard/ws/ai-jesus

## Testing Commands

```bash
# Test health endpoint
curl http://localhost:8081/

# Test metrics endpoint
curl http://localhost:8081/api/metrics/ai-jesus

# Test with formatted JSON
curl http://localhost:8081/api/metrics/ai-jesus | python -m json.tool
```

## Expected Responses

**Health Check:**
```json
{"status":"healthy","service":"variant-dashboard-api"}
```

**Metrics:**
```json
{
  "summary": {"total_variants": 0, "avg_engagement_rate": 0.0},
  "active_variants": [],
  "performance_leaders": [],
  "early_kills_today": {"kills_today": 0, "avg_time_to_kill_minutes": 0},
  "pattern_fatigue_warnings": [],
  "optimization_opportunities": [],
  "real_time_feed": []
}
```

## Troubleshooting

- **"Connection refused"**: Server is not running
- **"Address already in use"**: Port 8081 is busy, kill existing processes:
  ```bash
  lsof -ti:8081 | xargs kill -9
  ```
- **Import errors**: Virtual environment not activated or dependencies not installed