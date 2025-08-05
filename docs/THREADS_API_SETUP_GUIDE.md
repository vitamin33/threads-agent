# Threads API Setup Guide

This guide will walk you through obtaining the necessary credentials to post to Threads (Meta) programmatically.

## Prerequisites

- A Facebook Developer account
- An Instagram Business or Creator account (Threads uses Instagram's infrastructure)
- Your Instagram account must be connected to Threads

## Step-by-Step Setup

### 1. Create a Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Choose "Business" as the app type
4. Fill in the app details:
   - App Name: "Threads Agent Publisher" (or your preferred name)
   - App Contact Email: Your email
   - App Purpose: "Business"
5. Click "Create App"

### 2. Configure Instagram Business Account

1. Go to your Instagram profile settings
2. Switch to a Professional Account (Business or Creator)
3. Connect your Instagram account to a Facebook Page (required for API access)

### 3. Add Instagram Basic Display API

1. In your Facebook App dashboard, go to "Add Product"
2. Find "Instagram Basic Display" and click "Set Up"
3. Click "Create New App"
4. Fill in the required fields:
   - Display Name: "Threads Publisher"
   - Redirect URI: `https://localhost:8000/auth/callback`
   - Deauthorize Callback URL: `https://localhost:8000/auth/deauthorize`

### 4. Generate Access Tokens

#### Step 4.1: Get App ID and Secret
1. Go to Settings → Basic
2. Copy your:
   - App ID
   - App Secret (click "Show")

#### Step 4.2: Get Instagram User ID
1. Go to Instagram Basic Display → Basic Display
2. Add Instagram Test Users
3. Click "Add Instagram Testers"
4. Enter your Instagram username
5. Accept the tester invite in Instagram (Settings → Apps and Websites)

#### Step 4.3: Generate User Token
1. Generate an authorization URL:
```
https://api.instagram.com/oauth/authorize
  ?client_id={app-id}
  &redirect_uri={redirect-uri}
  &scope=threads_basic,threads_publish,threads_manage_insights
  &response_type=code
```

2. Visit this URL in your browser
3. Authorize the app
4. You'll be redirected to your redirect URI with a code parameter
5. Copy the code from the URL

#### Step 4.4: Exchange Code for Token
Run this curl command (or use Python):
```bash
curl -X POST https://api.instagram.com/oauth/access_token \
  -F client_id={app-id} \
  -F client_secret={app-secret} \
  -F grant_type=authorization_code \
  -F redirect_uri={redirect-uri} \
  -F code={code}
```

This returns:
```json
{
  "access_token": "IGQVJ...",
  "user_id": 17841401234567890
}
```

### 5. Get Long-Lived Access Token

Short-lived tokens expire in 1 hour. Exchange for a long-lived token (60 days):

```bash
curl -X GET "https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret={app-secret}&access_token={short-lived-token}"
```

### 6. Get Threads User ID

```bash
curl -X GET "https://graph.threads.net/v1.0/me?fields=id,username&access_token={access-token}"
```

This returns your Threads-specific user ID.

## Setting Environment Variables

Add these to your `.env` file:

```bash
# Threads API Configuration
THREADS_ACCESS_TOKEN=IGQVJXxxxxxxxxxxxxxxxx  # Your long-lived access token
THREADS_USER_ID=123456789012345              # Your Threads user ID
THREADS_USERNAME=yourusername                # Your Threads username
```

## Python Test Script

Create `test_threads_api.py`:

```python
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_threads_post():
    access_token = os.getenv("THREADS_ACCESS_TOKEN")
    user_id = os.getenv("THREADS_USER_ID")
    
    if not access_token or not user_id:
        print("❌ Missing Threads credentials in .env")
        return
    
    # Test post
    text = "🚀 Testing Threads API integration from threads-agent! #automation #api"
    
    async with httpx.AsyncClient() as client:
        # Create media container
        create_response = await client.post(
            f"https://graph.threads.net/v1.0/{user_id}/threads",
            params={
                "media_type": "TEXT",
                "text": text,
                "access_token": access_token
            }
        )
        
        if create_response.status_code != 200:
            print(f"❌ Failed to create thread: {create_response.text}")
            return
            
        media_id = create_response.json()["id"]
        
        # Publish the post
        publish_response = await client.post(
            f"https://graph.threads.net/v1.0/{user_id}/threads_publish",
            params={
                "creation_id": media_id,
                "access_token": access_token
            }
        )
        
        if publish_response.status_code == 200:
            result = publish_response.json()
            print(f"✅ Successfully posted to Threads!")
            print(f"Post ID: {result.get('id')}")
            print(f"URL: https://www.threads.net/@{os.getenv('THREADS_USERNAME')}/post/{result.get('id')}")
        else:
            print(f"❌ Failed to publish: {publish_response.text}")

# Run: python -m asyncio test_threads_api.py
```

## Token Refresh Strategy

Long-lived tokens expire after 60 days. Implement automatic refresh:

```python
async def refresh_threads_token(current_token: str) -> str:
    """Refresh token before expiry"""
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.instagram.com/refresh_access_token",
            params={
                "grant_type": "ig_refresh_token",
                "access_token": current_token
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            new_token = data["access_token"]
            expires_in = data["expires_in"]  # Seconds until expiry
            
            # Save new token to database or env
            return new_token
        else:
            raise Exception(f"Token refresh failed: {response.text}")
```

## Common Issues & Solutions

### Issue 1: "Invalid OAuth 2.0 Access Token"
- **Solution**: Ensure you're using the long-lived token, not the short-lived one

### Issue 2: "The user is not an Instagram Business"
- **Solution**: Convert your Instagram account to Business/Creator account

### Issue 3: "Insufficient developer role"
- **Solution**: Make sure your account has proper permissions in the Facebook app

### Issue 4: Rate Limiting
- **Solution**: Threads API has rate limits. Implement exponential backoff:
```python
import asyncio

async def post_with_retry(content, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await post_to_threads(content)
        except RateLimitError:
            wait_time = 2 ** attempt  # Exponential backoff
            await asyncio.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

## API Limitations

1. **Text Posts**: Maximum 500 characters
2. **Rate Limits**: ~200 posts per hour
3. **Media Types**: TEXT, IMAGE, VIDEO, CAROUSEL
4. **No Direct Replies**: Can't reply to other users' threads via API
5. **No Stories**: API doesn't support Threads stories

## Next Steps

1. Add credentials to `.env` file
2. Run the test script to verify setup
3. Enable auto-posting in tech_doc_generator:
   ```bash
   curl -X POST http://localhost:8000/api/auto-publish/achievement-content \
     -H "Content-Type: application/json" \
     -d '{"platforms": ["threads", "devto"], "test_mode": false}'
   ```

## Resources

- [Threads API Documentation](https://developers.facebook.com/docs/threads)
- [Instagram Basic Display API](https://developers.facebook.com/docs/instagram-basic-display-api)
- [Meta for Developers](https://developers.facebook.com/)