"""Client for interacting with the Threads Adaptor service."""
import httpx
from typing import Dict, Any, Optional


class ThreadsClient:
    """Client for Threads Adaptor API."""
    
    def __init__(self, base_url: str = "http://threads-adaptor:8070"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def get_post_performance(self, post_id: str) -> Dict[str, Any]:
        """Get performance metrics for a post."""
        response = await self.client.get(f"{self.base_url}/engagement/{post_id}")
        response.raise_for_status()
        data = response.json()
        
        return {
            "views": data.get("impressions_count", 0),
            "interactions": data.get("likes_count", 0) + data.get("comments_count", 0) + data.get("shares_count", 0),
            "engagement_rate": data.get("engagement_rate", 0.0)
        }
    
    async def delete_post(self, post_id: str) -> bool:
        """Delete a post from Threads (not implemented in current API)."""
        # This would need to be implemented in the threads_adaptor
        # For now, just return True to indicate success
        return True
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()