"""Revenue service integration for content pipeline"""

import os
from typing import Any, Dict, Optional

import httpx

REVENUE_SERVICE_URL = os.getenv("REVENUE_SERVICE_URL", "http://revenue:8080")


def enhance_content_with_revenue(
    content: str, persona_id: str, content_id: int, category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enhance content with revenue-generating elements:
    1. Inject contextual affiliate links
    2. Add lead capture CTAs based on content type

    Returns enhanced content and metadata
    """
    try:
        # Step 1: Inject affiliate links
        affiliate_response = httpx.post(
            f"{REVENUE_SERVICE_URL}/revenue/inject-affiliate-links",
            json={
                "content": content,
                "category": category,
                "content_id": content_id,
                "max_links": 2,  # Conservative to avoid being spammy
            },
            timeout=5.0,
        )

        if affiliate_response.status_code == 200:
            affiliate_result = affiliate_response.json()
            enhanced_content = affiliate_result["enhanced_content"]
            injected_links = affiliate_result["injected_links"]
        else:
            enhanced_content = content
            injected_links = []

        # Step 2: Add lead capture CTA based on persona
        lead_ctas = {
            "ai-jesus": "\n\n🙏 Join our community for daily AI wisdom → threads-agent.com/wisdom",
            "ai-elon": "\n\n🚀 Get the Mars colonization blueprint → threads-agent.com/mars",
            "default": "\n\n✨ Level up your content game → threads-agent.com/pro",
        }

        cta = lead_ctas.get(persona_id, lead_ctas["default"])

        # Only add CTA if content doesn't already have one
        if "threads-agent.com" not in enhanced_content:
            enhanced_content += cta

        return {
            "enhanced_content": enhanced_content,
            "revenue_metadata": {
                "affiliate_links": injected_links,
                "lead_capture_cta": cta.strip(),
                "content_id": content_id,
            },
        }

    except Exception as e:
        print(f"Revenue enhancement failed: {e}")
        # Return original content if enhancement fails
        return {"enhanced_content": content, "revenue_metadata": {}}


def track_content_performance(
    content_id: int, persona_id: str, engagement_metrics: Dict[str, Any]
) -> None:
    """
    Track content performance for revenue attribution
    This would be called after content is published and engagement is measured
    """
    try:
        # In a real implementation, this would:
        # 1. Track which content drives the most leads
        # 2. Attribute affiliate clicks/conversions to content
        # 3. Calculate ROI per content piece
        # 4. Feed back into content generation for optimization

        print(f"Tracking performance for content {content_id}")

    except Exception as e:
        print(f"Performance tracking failed: {e}")


def categorize_content(user_input: str) -> Optional[str]:
    """
    Categorize content based on user input to determine relevant affiliate categories
    """
    # Simple keyword-based categorization
    input_lower = user_input.lower()

    if any(keyword in input_lower for keyword in ["ai", "gpt", "claude", "automation"]):
        return "ai_tools"
    elif any(
        keyword in input_lower for keyword in ["productivity", "efficiency", "workflow"]
    ):
        return "productivity"
    elif any(
        keyword in input_lower for keyword in ["business", "startup", "entrepreneur"]
    ):
        return "business"
    elif any(keyword in input_lower for keyword in ["learn", "course", "education"]):
        return "learning"

    return None
