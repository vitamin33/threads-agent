import json
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from services.revenue.db.models import AffiliateLink, RevenueEvent


@dataclass
class AffiliateMerchant:
    name: str
    base_url: str
    ref_param: str = "ref"
    category: str = "general"


class AffiliateLinkInjector:
    """Manages contextual affiliate link injection into content"""

    def __init__(self, db: Session, affiliate_id: str = "viral123"):
        self.db = db
        self.affiliate_id = affiliate_id

        # Initialize affiliate merchant database
        self.affiliate_db = {
            "ai_tools": {
                "claude": AffiliateMerchant(
                    "claude", "https://anthropic.com/claude", "ref", "ai_tools"
                ),
                "chatgpt": AffiliateMerchant(
                    "chatgpt", "https://openai.com/chatgpt", "ref", "ai_tools"
                ),
                "midjourney": AffiliateMerchant(
                    "midjourney", "https://midjourney.com", "ref", "ai_tools"
                ),
                "perplexity": AffiliateMerchant(
                    "perplexity", "https://perplexity.ai", "ref", "ai_tools"
                ),
            },
            "productivity": {
                "notion": AffiliateMerchant(
                    "notion", "https://notion.so", "ref", "productivity"
                ),
                "obsidian": AffiliateMerchant(
                    "obsidian", "https://obsidian.md", "ref", "productivity"
                ),
                "todoist": AffiliateMerchant(
                    "todoist", "https://todoist.com", "ref", "productivity"
                ),
                "calendly": AffiliateMerchant(
                    "calendly", "https://calendly.com", "ref", "productivity"
                ),
            },
            "business": {
                "stripe": AffiliateMerchant(
                    "stripe", "https://stripe.com", "ref", "business"
                ),
                "shopify": AffiliateMerchant(
                    "shopify", "https://shopify.com", "ref", "business"
                ),
                "mailchimp": AffiliateMerchant(
                    "mailchimp", "https://mailchimp.com", "ref", "business"
                ),
            },
            "learning": {
                "coursera": AffiliateMerchant(
                    "coursera", "https://coursera.org", "ref", "learning"
                ),
                "udemy": AffiliateMerchant(
                    "udemy", "https://udemy.com", "ref", "learning"
                ),
                "masterclass": AffiliateMerchant(
                    "masterclass", "https://masterclass.com", "ref", "learning"
                ),
            },
        }

        # Keywords that trigger affiliate link consideration
        self.keyword_map = {
            "ai": ["ai_tools"],
            "artificial intelligence": ["ai_tools"],
            "chatbot": ["ai_tools"],
            "language model": ["ai_tools"],
            "productivity": ["productivity"],
            "task management": ["productivity"],
            "note taking": ["productivity"],
            "payment": ["business"],
            "e-commerce": ["business"],
            "online store": ["business"],
            "learning": ["learning"],
            "course": ["learning"],
            "education": ["learning"],
        }

    def analyze_content_topics(self, content: str) -> List[str]:
        """Analyze content and determine relevant affiliate categories"""
        content_lower = content.lower()
        relevant_categories = set()

        # Check for keywords
        for keyword, categories in self.keyword_map.items():
            if keyword in content_lower:
                relevant_categories.update(categories)

        # Also check for specific merchant names
        for category, merchants in self.affiliate_db.items():
            for merchant_key, merchant in merchants.items():
                if merchant_key in content_lower or merchant.name in content_lower:
                    relevant_categories.add(category)

        return list(relevant_categories)

    def generate_affiliate_url(
        self, merchant: AffiliateMerchant, content_id: Optional[int] = None
    ) -> str:
        """Generate trackable affiliate URL"""
        # Build affiliate URL with tracking parameters
        separator = "&" if "?" in merchant.base_url else "?"
        affiliate_url = (
            f"{merchant.base_url}{separator}{merchant.ref_param}={self.affiliate_id}"
        )

        # Add content tracking if available
        if content_id:
            affiliate_url += f"&content_id={content_id}"

        return affiliate_url

    def inject_contextual_links(
        self,
        content: str,
        topic_category: Optional[str] = None,
        content_id: Optional[int] = None,
        max_links: int = 3,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Inject contextual affiliate links into content
        Returns: (enhanced_content, list_of_injected_links)
        """
        # Analyze content if category not provided
        if not topic_category:
            categories = self.analyze_content_topics(content)
            topic_category = categories[0] if categories else "general"

        enhanced_content = content
        injected_links = []
        link_count = 0

        # Get relevant merchants for the category
        if topic_category in self.affiliate_db:
            merchants = self.affiliate_db[topic_category]

            for merchant_key, merchant in merchants.items():
                if link_count >= max_links:
                    break

                # Look for natural mentions of the merchant
                pattern = rf"\b{re.escape(merchant.name)}\b"
                if re.search(pattern, content, re.IGNORECASE):
                    # Generate affiliate URL
                    affiliate_url = self.generate_affiliate_url(merchant, content_id)

                    # Store link in database
                    affiliate_link = AffiliateLink(  # type: ignore[call-arg]
                        content_id=content_id,
                        link_url=affiliate_url,
                        category=merchant.category,
                        merchant=merchant.name,
                    )
                    self.db.add(affiliate_link)
                    self.db.flush()  # Flush to get the ID

                    # Replace first occurrence with linked version
                    replacement = f"[{merchant.name}]({affiliate_url})"
                    enhanced_content = re.sub(
                        pattern,
                        replacement,
                        enhanced_content,
                        count=1,
                        flags=re.IGNORECASE,
                    )

                    injected_links.append(
                        {
                            "merchant": merchant.name,
                            "url": affiliate_url,
                            "category": merchant.category,
                            "link_id": affiliate_link.id,
                        }
                    )
                    link_count += 1

        # Add subtle CTA if links were injected
        if injected_links and not re.search(
            r"affiliate|commission|earn", content, re.IGNORECASE
        ):
            enhanced_content += "\n\n_✨ Some links help support our content creation_"

        # Commit to save affiliate links
        self.db.commit()

        # Record metrics (using content_quality as a placeholder)
        # record_business_metric("content_quality", value=float(len(injected_links)))

        return enhanced_content, injected_links

    def track_click(self, link_id: int, referrer: Optional[str] = None) -> bool:
        """Track affiliate link click"""
        try:
            link = self.db.query(AffiliateLink).filter_by(id=link_id).first()
            if link:
                link.click_count += 1

                # Record revenue event
                event = RevenueEvent(  # type: ignore[call-arg]
                    event_type="affiliate_click",
                    amount=0.00,  # Clicks don't generate immediate revenue
                    content_id=link.content_id,
                    event_metadata=json.dumps(
                        {
                            "link_id": link_id,
                            "merchant": link.merchant,
                            "referrer": referrer,
                        }
                    ),
                )
                self.db.add(event)
                self.db.commit()

                # Record metrics - disabled for now
                # record_business_metric("content_quality", value=1.0)

                return True
        except Exception as e:
            self.db.rollback()
            print(f"Error tracking click: {e}")

        return False

    def track_conversion(
        self,
        link_id: int,
        commission_amount: float,
        customer_email: Optional[str] = None,
    ) -> bool:
        """Track affiliate conversion and commission"""
        try:
            link = self.db.query(AffiliateLink).filter_by(id=link_id).first()
            if link:
                link.conversion_count += 1
                link.revenue_generated += Decimal(str(commission_amount))

                # Record revenue event
                event = RevenueEvent(  # type: ignore[call-arg]
                    event_type="affiliate_commission",
                    amount=commission_amount,
                    customer_email=customer_email,
                    content_id=link.content_id,
                    event_metadata=json.dumps(
                        {"link_id": link_id, "merchant": link.merchant}
                    ),
                )
                self.db.add(event)
                self.db.commit()

                # Record metrics - disabled for now
                # record_business_metric("content_quality", value=1.0)

                return True
        except Exception as e:
            self.db.rollback()
            print(f"Error tracking conversion: {e}")

        return False

    def get_top_performing_links(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing affiliate links by revenue"""
        links = (
            self.db.query(AffiliateLink)
            .order_by(AffiliateLink.revenue_generated.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": link.id,
                "merchant": link.merchant,
                "category": link.category,
                "clicks": link.click_count,
                "conversions": link.conversion_count,
                "revenue": float(link.revenue_generated),
                "conversion_rate": (
                    (link.conversion_count / link.click_count * 100)
                    if link.click_count > 0
                    else 0
                ),
            }
            for link in links
        ]
