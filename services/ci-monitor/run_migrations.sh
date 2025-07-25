#!/bin/bash
set -e

# Get postgres password
POSTGRES_PASSWORD=$(kubectl get secret threads-postgresql -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)

# Run migrations using orchestrator pod
kubectl exec deploy/orchestrator -- sh -c "
export POSTGRES_DSN='postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/threads_agent'
export DATABASE_URL='postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/threads_agent'
export PYTHONPATH='/app'
cd /app/services/orchestrator
alembic -c db/alembic.ini upgrade head
"