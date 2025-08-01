# Real-Time Variant Performance Dashboard API

A FastAPI-based backend service providing real-time monitoring and analytics for variant performance in the threads-agent system.

## Features

- **Real-time WebSocket Updates**: Live performance metrics pushed to connected dashboards
- **Comprehensive Metrics API**: Aggregated variant performance data
- **Early Kill Monitoring**: Real-time notifications when variants are terminated
- **Pattern Fatigue Detection**: Warnings for overused content patterns
- **Optimization Suggestions**: AI-driven recommendations for improving performance

## Architecture

```
dashboard_api/
├── main.py                 # FastAPI application
├── variant_metrics.py      # Core metrics API logic
├── websocket_handler.py    # WebSocket connection management
├── event_processor.py      # Event processing from monitoring systems
└── tests/                  # Comprehensive test suite
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head
```

## Running the Service

```bash
# Development mode
uvicorn main:app --host 0.0.0.0 --port 8081 --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8081 --workers 4
```

## API Endpoints

### REST Endpoints

- `GET /` - Health check
- `GET /api/metrics/{persona_id}` - Get comprehensive metrics for a persona
- `GET /api/variants/{persona_id}/active` - Get active variants with performance
- `GET /api/optimization/{persona_id}` - Get optimization suggestions
- `POST /api/events/early-kill` - Handle early kill events
- `POST /api/events/performance-update` - Handle performance updates

### WebSocket Endpoint

- `WS /dashboard/ws/{persona_id}` - Real-time dashboard updates

## WebSocket Protocol

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8081/dashboard/ws/ai-jesus');
```

### Message Types

**Initial Data** (sent on connection):
```json
{
  "type": "initial_data",
  "data": {
    "summary": {...},
    "active_variants": [...],
    "optimization_opportunities": [...]
  }
}
```

**Variant Update**:
```json
{
  "type": "variant_update",
  "timestamp": "2025-01-31T10:00:00Z",
  "data": {
    "event_type": "performance_update",
    "variant_id": "var_123",
    "current_er": 0.065
  }
}
```

## Integration with Monitoring Systems

The dashboard integrates with:
- **EarlyKillMonitor**: Receives notifications when variants are terminated
- **PatternFatigueDetector**: Gets warnings about overused patterns
- **PerformanceMonitor**: Real-time variant performance metrics

## Testing

```bash
# Run all tests
python test_runner.py all

# Quick test suite
python test_runner.py quick

# Specific test categories
python test_runner.py unit
python test_runner.py integration
python test_runner.py performance
```

## Configuration

Environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for caching
- `LOG_LEVEL`: Logging level (default: INFO)

## Performance

- Supports 500+ concurrent WebSocket connections
- Sub-second latency for real-time updates
- Handles 1000+ active variants per persona
- Memory-efficient with bounded caching

## Development

See [README_TESTING.md](./README_TESTING.md) for comprehensive testing documentation.