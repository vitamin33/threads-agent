# M1: Telemetry System Documentation

> **🎯 Goal**: Measure everything to optimize development efficiency by 15-30%

## Quick Start

```bash
# 1. Initialize telemetry
just dev-system init --telemetry

# 2. Check daily metrics
just metrics-today

# 3. View different periods
just dev-system metrics --period 7d
just dev-system metrics --period 30d
```

## Integration Patterns

### Option 1: Decorator Integration (Recommended)

```python
from dev_system.ops.telemetry import telemetry_decorator, openai_cost_calculator

# For model calls (OpenAI, etc.)
@telemetry_decorator(
    agent_name="persona_runtime",
    event_type="model_call",
    cost_calculator=openai_cost_calculator
)
def generate_content(prompt: str):
    response = openai.chat.completions.create(...)
    return response

# For tool calls
@telemetry_decorator(
    agent_name="orchestrator",
    event_type="tool_call"
)
def process_request(data: dict):
    # Your processing logic
    return result
```

### Option 2: Service-Specific Helpers

```python
from dev_system.ops.integration import (
    orchestrator_telemetry,
    persona_runtime_telemetry,
    viral_engine_telemetry
)

@persona_runtime_telemetry
def my_ai_function():
    pass
```

### Option 3: Auto-Integration

```python
from dev_system.ops.integration import auto_integrate_service
import my_service_module

# Automatically wraps functions with AI-related names
auto_integrate_service("my_service", my_service_module)
```

## What Gets Tracked

- **Success Rate**: Percentage of successful calls
- **P95 Latency**: 95th percentile response time
- **Total Cost**: Token usage costs (OpenAI, etc.)
- **Top Agent**: Most active service
- **Failed Calls**: Error count and types
- **Alerts**: Automatic threshold warnings

## Database Schema

SQLite database at `.dev-system/data/telemetry.db`:

```sql
CREATE TABLE telemetry_events (
    id INTEGER PRIMARY KEY,
    timestamp REAL NOT NULL,
    event_type TEXT NOT NULL,      -- model_call, tool_call, api_call
    agent_name TEXT NOT NULL,      -- orchestrator, persona_runtime, etc.
    function_name TEXT NOT NULL,   -- generate_content, process_task, etc.
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    latency_ms REAL NOT NULL,
    cost_usd REAL DEFAULT 0.0,
    success BOOLEAN NOT NULL,
    error_type TEXT,               -- Exception class name if failed
    trace_id TEXT,                 -- For distributed tracing
    metadata TEXT,                 -- JSON additional data
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Cost Calculation

Built-in cost calculators:

```python
from dev_system.ops.telemetry import openai_cost_calculator

def custom_cost_calculator(result):
    # Your custom logic
    return cost_in_usd
```

## Alert Thresholds

Automatic alerts when:
- Success rate < 90%
- P95 latency > 3000ms  
- Daily cost > $10.00

## Business Value

**Immediate benefits:**
- **Spot performance regressions** before they impact users
- **Optimize token usage** by identifying expensive operations
- **Track agent efficiency** across different tasks
- **Debug failures** with detailed error tracking

**Weekly time savings:**
- 2-4 hours saved on debugging and optimization
- ROI payback in 2-8 weeks
- Foundation for advanced optimizations

## Example Output

```
📊 Development Metrics (Last 1 day)
==================================================
Success Rate: 92.5%
P95 Latency: 1,245ms
Total Cost: $3.47
Top Agent: persona_runtime
Failed Calls: 12

🚨 Alerts:
  - High P95 latency: 1,245ms
```

## Integration Examples

See `example_integration.py` for:
- Mock model calls with realistic timing
- Cost calculation examples
- Error simulation
- Sample data generation

## Advanced Usage

### Custom Event Types

```python
@telemetry_decorator(
    agent_name="my_service",
    event_type="custom_operation"
)
def my_function():
    pass
```

### Trace ID Propagation

```python
def parent_function():
    trace_id = f"trace_{int(time.time())}"
    child_function(_trace_id=trace_id)

@telemetry_decorator(agent_name="service")
def child_function():
    pass  # Will inherit trace_id from kwargs
```

### Metadata Enrichment

```python
@telemetry_decorator(agent_name="service")  
def enriched_function(user_id: str):
    # Function args automatically captured in metadata
    pass
```

This telemetry system provides the foundation for data-driven development optimization and sets up M2 quality gates.