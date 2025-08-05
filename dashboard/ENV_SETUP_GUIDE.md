# Dashboard Environment Configuration Guide

This guide explains how to configure the Streamlit dashboard to connect to your Threads Agent services in different environments.

## Quick Setup

1. Copy the example file:
   ```bash
   cd dashboard
   cp .env.example .env
   ```

2. Edit `.env` based on your environment (see scenarios below)

## Configuration Scenarios

### 🖥️ Scenario 1: Local Development (Most Common)

**When to use**: Running dashboard locally with services in k3d cluster

1. First, start your services and create port forwards:
   ```bash
   # In terminal 1 - Start services
   just dev-start
   
   # In terminal 2 - Create port forwards
   kubectl port-forward svc/achievement-collector 8000:8000 &
   kubectl port-forward svc/tech-doc-generator 8001:8001 &
   kubectl port-forward svc/orchestrator 8080:8080 &
   kubectl port-forward svc/viral-engine 8003:8003 &
   ```

2. Your `.env` file should have:
   ```env
   ACHIEVEMENT_API_URL=http://localhost:8000
   TECH_DOC_API_URL=http://localhost:8001
   ORCHESTRATOR_URL=http://localhost:8080
   VIRAL_ENGINE_URL=http://localhost:8003
   ```

3. Run the dashboard:
   ```bash
   just ui-dashboard
   ```

### 🐳 Scenario 2: Docker Compose

**When to use**: Running everything with docker-compose

1. Your `.env` file should use service names:
   ```env
   ACHIEVEMENT_API_URL=http://achievement-collector:8000
   TECH_DOC_API_URL=http://tech-doc-generator:8001
   ORCHESTRATOR_URL=http://orchestrator:8080
   VIRAL_ENGINE_URL=http://viral-engine:8003
   ```

2. Run with:
   ```bash
   just ui-docker
   ```

### ☸️ Scenario 3: Kubernetes Deployment

**When to use**: Dashboard deployed inside the k8s cluster

1. Your `.env` file (or ConfigMap) should use Kubernetes service names:
   ```env
   ACHIEVEMENT_API_URL=http://achievement-collector:8000
   TECH_DOC_API_URL=http://tech-doc-generator:8001
   ORCHESTRATOR_URL=http://orchestrator:8080
   VIRAL_ENGINE_URL=http://viral-engine:8003
   ```

2. Deploy and access:
   ```bash
   just ui-deploy
   just ui-port-forward
   ```

## Environment Variables Explained

| Variable | Purpose | Example Value |
|----------|---------|---------------|
| `ACHIEVEMENT_API_URL` | Achievement collector service | `http://localhost:8000` |
| `TECH_DOC_API_URL` | Tech doc generator service | `http://localhost:8001` |
| `ORCHESTRATOR_URL` | Main orchestrator service | `http://localhost:8080` |
| `VIRAL_ENGINE_URL` | Viral content engine | `http://localhost:8003` |

## Troubleshooting

### Dashboard can't connect to services?

1. **Check port forwards are running**:
   ```bash
   ps aux | grep "port-forward"
   ```

2. **Verify services are healthy**:
   ```bash
   kubectl get pods
   curl http://localhost:8000/health
   ```

3. **Check .env file is loaded**:
   - The dashboard reads from `dashboard/.env`
   - Make sure you're in the right directory

### Using custom service URLs?

If your services are deployed elsewhere (e.g., staging), update the URLs:

```env
ACHIEVEMENT_API_URL=https://achievement-api.your-domain.com
TECH_DOC_API_URL=https://tech-doc-api.your-domain.com
# etc...
```

## Best Practices

1. **Never commit `.env`** - It's in `.gitignore`
2. **Use `.env.example`** as reference
3. **Different `.env` files** for different environments
4. **In production**, use Kubernetes ConfigMaps or Secrets instead of `.env` files