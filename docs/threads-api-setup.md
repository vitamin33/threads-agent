# Threads API Integration Setup Guide

This guide walks you through setting up the real Threads API integration to replace the fake-threads service.

## Prerequisites

1. A Meta/Facebook Developer Account
2. A Threads account (username)
3. An Instagram Professional or Business account linked to your Threads account

## Step 1: Create a Meta App

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click "My Apps" → "Create App"
3. Choose "Business" as the app type
4. Fill in the app details:
   - App Name: "Threads Agent Stack"
   - App Contact Email: your email
   - Business Account: Select or create one

## Step 2: Add Threads API Product

1. In your app dashboard, click "Add Product"
2. Find "Threads" and click "Set Up"
3. Accept the Threads API Terms of Service

## Step 3: Configure OAuth Redirect

1. In Threads API settings, add OAuth redirect URI:
   ```
   https://localhost:8080/auth/callback
   ```
2. For production, add your actual domain

## Step 4: Get Access Token

### Option A: Using Graph API Explorer (Development)

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from the dropdown
3. Click "Get User Access Token"
4. Select these permissions:
   - `threads_basic`
   - `threads_content_publish`
   - `threads_manage_insights`
   - `threads_manage_replies`
   - `threads_read_replies`
5. Click "Generate Access Token"
6. Copy the token (valid for ~1 hour)

### Option B: Long-Lived Token (Production)

1. Exchange short-lived token for long-lived:
   ```bash
   curl -X GET "https://graph.threads.net/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-lived-token}"
   ```

2. The response contains a long-lived token (valid for ~60 days)

## Step 5: Get User ID

```bash
curl -X GET "https://graph.threads.net/v1.0/me?access_token={your-access-token}"
```

Save the `id` from the response.

## Step 6: Configure Threads Adaptor

### For Development (values-dev.yaml)

```yaml
threadsAdaptor:
  enabled: true
  credentials:
    appId: "YOUR_APP_ID"
    appSecret: "YOUR_APP_SECRET"
    accessToken: "YOUR_ACCESS_TOKEN"
    userId: "YOUR_USER_ID"

# Disable fake-threads since we're using real API
fakeThreads:
  enabled: false
```

### For Production (values-prod.yaml)

Use Kubernetes secrets:

```bash
kubectl create secret generic threads-api-credentials \
  --from-literal=THREADS_APP_ID="YOUR_APP_ID" \
  --from-literal=THREADS_APP_SECRET="YOUR_APP_SECRET" \
  --from-literal=THREADS_ACCESS_TOKEN="YOUR_ACCESS_TOKEN" \
  --from-literal=THREADS_USER_ID="YOUR_USER_ID"
```

## Step 7: Deploy and Test

```bash
# Build the threads-adaptor image
docker build -f services/threads_adaptor/Dockerfile -t threads-adaptor:local .

# Import to k3d
k3d image import threads-adaptor:local -c dev

# Deploy with threads-adaptor enabled
just deploy-dev

# Test the integration
kubectl port-forward svc/threads-adaptor 8080:8080
curl http://localhost:8080/health
```

## Step 8: Test Publishing

```bash
# Create a test post
curl -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI productivity",
    "content": "Testing Threads API integration! 🚀",
    "persona_id": "ai-jesus"
  }'
```

## Rate Limits

The Threads API has the following rate limits:
- 20 API calls per minute (configured by default)
- 250 API calls per hour
- Content publishing: 100 posts per 24 hours

The threads-adaptor service includes automatic rate limiting and exponential backoff.

## Monitoring

Check engagement metrics:
```bash
# Get metrics for a specific post
curl http://localhost:8080/metrics/{thread-id}

# Refresh all metrics
curl -X POST http://localhost:8080/refresh-metrics

# View in Grafana
just grafana
```

## Troubleshooting

### "Missing Threads API credentials"
- Ensure all environment variables are set in your values file
- Check the secret is created: `kubectl get secret threads-api-credentials`

### "API returned 401"
- Your access token may have expired
- Generate a new token and update the secret

### "Rate limit exceeded"
- The service automatically handles rate limits with backoff
- Check `THREADS_RATE` environment variable (default: 20/min)

### No engagement data
- Threads API may take 5-15 minutes to return initial metrics
- The service automatically fetches metrics after a 5-minute delay
- Use `/refresh-metrics` to manually update

## Migration from fake-threads

1. Enable both services temporarily:
   ```yaml
   fakeThreads:
     enabled: true
   threadsAdaptor:
     enabled: true
   ```

2. Update celery-worker to use threads-adaptor (already done in templates)

3. Test with a few posts to ensure everything works

4. Disable fake-threads:
   ```yaml
   fakeThreads:
     enabled: false
   ```

## Security Best Practices

1. **Never commit credentials** to git
2. Use Kubernetes secrets for production
3. Rotate access tokens regularly (every 60 days)
4. Monitor API usage in Meta Developer Dashboard
5. Set up webhook notifications for token expiry

## Next Steps

1. Set up automated token refresh
2. Implement webhook handlers for real-time engagement updates
3. Add support for media posts (images/videos)
4. Implement reply management
5. Set up A/B testing for different posting times
