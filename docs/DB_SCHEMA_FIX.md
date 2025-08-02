# Database Schema Fix: Expand business_value Column

## Problem
The enhanced business value calculator generates detailed JSON objects that exceed the current `VARCHAR(255)` limit:

**Error**: `value too long for type character varying(255)`

**Example JSON (284 characters)**:
```json
{
  "total_value": 156000,
  "currency": "USD", 
  "period": "yearly",
  "type": "time_savings",
  "confidence": 0.7,
  "method": "time_calculation",
  "breakdown": {
    "hours_saved_annually": 1248.0,
    "hourly_rate": 125.0,
    "role_assumed": "senior",
    "team_multiplier": 6,
    "base_hours_per_person": 208.0
  }
}
```

## Solution
Expand `business_value` column from `VARCHAR(255)` to `TEXT` type to handle large JSON objects.

## Changes Made

### 1. Achievement Model Update
```python
# Before
business_value = Column(String(255))  # Business value description

# After  
business_value = Column(Text)  # Business value JSON (can be large)
```

### 2. Alembic Migration (Achievement Collector)
Created `002_expand_business_value_column.py`:
- Upgrades: `VARCHAR(255)` → `TEXT`
- Downgrades: `TEXT` → `VARCHAR(255)` (with data truncation warning)

### 3. Alembic Migration (Orchestrator) 
Created `expand_business_value_column.py`:
- Preventive migration for orchestrator service
- Handles missing table/column gracefully

## Impact
- **Before**: Database error on JSON > 255 characters
- **After**: Can store detailed business value breakdowns of any size
- **Backward Compatible**: Existing short values continue to work
- **No Data Loss**: Migration preserves existing data

## Test Case Success
After this fix, the enhanced business value calculation should successfully store:
```json
{
  "total_value": 156000,  // $156,000/year
  "method": "time_calculation",  // Complex calculation 
  "team_multiplier": 6,  // 6-person team detection
  "confidence": 0.7  // Medium confidence for calculated values
}
```

## Migration Commands
```bash
# Achievement Collector Service
cd services/achievement_collector
alembic upgrade head

# Orchestrator Service (if needed)
cd services/orchestrator  
alembic upgrade head
```