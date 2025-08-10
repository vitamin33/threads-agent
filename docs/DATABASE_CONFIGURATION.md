# Database Configuration Guide

## Overview

This document explains the centralized database configuration approach used in the threads-agent project to prevent configuration inconsistencies.

## Configuration Sources

### 1. Helm Values (Kubernetes Deployments)

The primary source of truth for database configuration in Kubernetes deployments:

```yaml
# chart/values.yaml (defaults)
postgres:
  auth:
    username: "postgres"
    postgresPassword: "pass"       # Override in production!
    database: "threads_agent"
```

### 2. Environment Variables

Services accept configuration through environment variables:

- `DATABASE_URL` - Standard PostgreSQL URL format: `postgresql://user:pass@host:port/database`
- `POSTGRES_DSN` - SQLAlchemy format: `postgresql+psycopg2://user:pass@host:port/database`

### 3. Centralized Python Module

Use the centralized configuration module for consistency:

```python
from services.common.database_config import db_config, get_postgres_dsn

# Get connection string
dsn = get_postgres_dsn()  # For SQLAlchemy
url = db_config.get_database_url()  # Standard format
```

## Helm Template Helpers

Use these helpers in Helm templates for consistency:

```yaml
env:
  - name: POSTGRES_DSN
    value: {{ include "threads.postgres.dsn" . | quote }}
  - name: DATABASE_URL
    value: {{ include "threads.database.url" . | quote }}
```

Available helpers:
- `threads.postgres.dsn` - SQLAlchemy format DSN
- `threads.database.url` - Standard database URL
- `threads.postgres.username` - Username only
- `threads.postgres.password` - Password only
- `threads.postgres.database` - Database name only

## Best Practices

1. **Always use the centralized configuration** - Don't hardcode database credentials
2. **Override in production** - Use Kubernetes secrets for production passwords
3. **Use helpers in Helm** - Ensures consistency across all deployments
4. **Import the config module** - For Python services, use `services.common.database_config`

## Migration Guide

If you have a service using hardcoded database configuration:

### Before:
```python
# Don't do this!
pg_dsn = "postgresql+psycopg2://postgres:pass@postgres:5432/threads_agent"
```

### After:
```python
# Do this instead
from services.common.database_config import get_postgres_dsn
pg_dsn = get_postgres_dsn()
```

## Environment-Specific Values

### Development (values-dev.yaml)
```yaml
postgres:
  enabled: true
  auth:
    postgresPassword: "dev_password"
```

### CI (values-ci.yaml)
```yaml
postgres:
  enabled: true
  auth:
    postgresPassword: "pass"  # Simple password for CI
```

### Production (values-prod.yaml)
```yaml
postgres:
  enabled: true
  auth:
    postgresPassword: ""  # Use Kubernetes secret instead
```

## Troubleshooting

### Service can't connect to database

1. Check environment variables:
   ```bash
   kubectl exec <pod> -- env | grep -E "DATABASE_URL|POSTGRES_DSN"
   ```

2. Verify values are consistent:
   ```bash
   helm get values <release> | grep -A5 postgres
   ```

3. Ensure database name matches:
   - Default: `threads_agent`
   - Must be consistent across all services

### Import errors in CI

If you see import errors related to database models:
1. Ensure database configuration is wrapped in try/except
2. Use the `DB_AVAILABLE` flag pattern shown in `scheduling_router.py`
3. Services should gracefully handle missing database in CI

## Security Notes

- **Never commit real passwords** to the repository
- Use Kubernetes secrets for production deployments
- Rotate passwords regularly
- Use different passwords for each environment