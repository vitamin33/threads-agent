#!/usr/bin/env python3
"""Test the manual LinkedIn publishing workflow"""

import asyncio
import json
from datetime import datetime
import sys
sys.path.append('.')

from app.models.article import ArticleContent, Platform
from app.services.manual_publisher import ManualPublishingTracker, LinkedInManualWorkflow

async def test_linkedin_workflow():
    """Test creating a LinkedIn draft for manual posting"""
    
    print("🚀 Testing Manual LinkedIn Publishing Workflow")
    print("=" * 60)
    
    # Create sample article content
    article = ArticleContent(
        title="How I Built an AI System That Measures Developer Impact",
        subtitle="Turn vague 'improved performance' claims into concrete $$ value",
        content="""
After years of struggling to quantify my impact in interviews, I built a system 
that automatically tracks and measures the business value of every PR I merge.

The Achievement Collector analyzes code changes, performance metrics, and business 
outcomes to generate concrete numbers like "Saved $312/month in infrastructure costs" 
or "Reduced API response time by 2.3 seconds, affecting 50k daily users."

Key features:
- Automatic PR analysis using AI
- Business value extraction 
- Performance metrics tracking
- Portfolio generation

This has transformed how I approach job interviews and performance reviews.
        """.strip(),
        insights=[
            "Every PR now has quantifiable business impact",
            "Reduced infrastructure costs by 38% through optimization tracking",
            "Interview success rate increased from 8% to 23%"
        ],
        tags=["python", "ai", "mlops", "career", "portfolio"],
        code_examples=[]
    )
    
    # Create draft using manual workflow
    tracker = ManualPublishingTracker(db=None)
    
    print("\n📝 Creating LinkedIn Draft...")
    draft_result = await tracker.create_draft(
        platform=Platform.LINKEDIN,
        content=article,
        formatted_content=LinkedInManualWorkflow.format_for_copy_paste(article)
    )
    
    print(f"\n✅ Draft Created!")
    print(f"Draft ID: {draft_result['draft_id']}")
    print(f"\n📋 Instructions:")
    for i, instruction in enumerate(draft_result['instructions'], 1):
        print(f"   {i}. {instruction}")
    
    print(f"\n📄 Formatted Content for LinkedIn:")
    print("-" * 60)
    print(draft_result['content'])
    print("-" * 60)
    
    # Simulate user posting and confirming
    print("\n⏳ Simulating manual posting...")
    await asyncio.sleep(2)
    
    # Confirm the post
    confirm_result = await tracker.confirm_manual_post(
        draft_id=draft_result['draft_id'],
        post_url="https://www.linkedin.com/posts/example-post-url"
    )
    
    print(f"\n✅ Post Confirmed!")
    print(f"Status: {confirm_result['message']}")
    print(f"\n📊 Next Steps:")
    for step in confirm_result['next_steps']:
        print(f"   • {step}")
    
    # Show analytics template
    print("\n📈 Analytics Template for Later:")
    template = LinkedInManualWorkflow.create_analytics_template()
    print(json.dumps(template['example'], indent=2))
    
    print("\n✨ Workflow Complete!")

if __name__ == "__main__":
    asyncio.run(test_linkedin_workflow())