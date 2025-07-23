import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import func
from sqlalchemy.orm import Session

from services.revenue.db.models import Customer, Lead, RevenueEvent


class LeadCapture:
    """Manages lead capture, scoring, and nurturing workflows"""

    def __init__(self, db: Session):
        self.db = db

        # Lead scoring rules
        self.scoring_rules = {
            "email_domain": {
                "corporate": 20,  # Corporate email addresses
                "gmail": 10,  # Gmail addresses
                "other": 5,  # Other providers
            },
            "source": {"organic": 15, "affiliate": 20, "direct": 10, "social": 12},
            "engagement": {
                "immediate": 25,  # Signed up within 1 min of viewing
                "quick": 15,  # Within 5 minutes
                "normal": 10,  # Within 30 minutes
                "delayed": 5,  # After 30 minutes
            },
            "content_type": {
                "viral": 20,  # From viral content
                "trending": 15,  # From trending content
                "regular": 10,  # Regular content
            },
        }

        # Email templates for nurturing sequences
        self.email_sequences = {
            "welcome": {
                "subject": "Welcome to Threads Agent Stack! 🚀",
                "delay_hours": 0,
                "priority": "high",
            },
            "value_prop": {
                "subject": "How to 10x Your Content Engagement",
                "delay_hours": 24,
                "priority": "medium",
            },
            "case_study": {
                "subject": "Case Study: From 0 to $20k MRR in 90 Days",
                "delay_hours": 72,
                "priority": "medium",
            },
            "offer": {
                "subject": "Special Offer: 30% Off Pro Plan",
                "delay_hours": 168,  # 7 days
                "priority": "high",
            },
        }

    def validate_and_score_email(self, email: str) -> Dict:
        """Validate email and calculate initial score"""
        try:
            # Validate email format
            validation = validate_email(email, check_deliverability=False)
            normalized_email = validation.email

            # Determine email domain type
            domain = normalized_email.split("@")[1].lower()
            domain_score = 0

            if domain == "gmail.com":
                domain_score = self.scoring_rules["email_domain"]["gmail"]
            elif domain in ["yahoo.com", "hotmail.com", "outlook.com"]:
                domain_score = self.scoring_rules["email_domain"]["other"]
            else:
                # Assume corporate email
                domain_score = self.scoring_rules["email_domain"]["corporate"]

            return {
                "valid": True,
                "normalized_email": normalized_email,
                "domain": domain,
                "domain_score": domain_score,
            }

        except EmailNotValidError as e:
            return {"valid": False, "error": str(e)}

    def capture_email(
        self,
        email: str,
        source: str,
        content_id: Optional[int] = None,
        utm_params: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Capture lead email with attribution tracking"""
        # Validate email
        validation = self.validate_and_score_email(email)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}

        normalized_email = validation["normalized_email"]

        # Check if lead already exists
        existing_lead = self.db.query(Lead).filter_by(email=normalized_email).first()
        if existing_lead:
            return {
                "success": False,
                "error": "Email already registered",
                "lead_id": existing_lead.id,
            }

        try:
            # Calculate lead score
            lead_score = validation["domain_score"]
            lead_score += self.scoring_rules["source"].get(source, 5)

            # Add engagement score based on metadata
            if metadata and "view_duration" in metadata:
                duration = metadata["view_duration"]
                if duration < 60:
                    lead_score += self.scoring_rules["engagement"]["immediate"]
                elif duration < 300:
                    lead_score += self.scoring_rules["engagement"]["quick"]
                elif duration < 1800:
                    lead_score += self.scoring_rules["engagement"]["normal"]
                else:
                    lead_score += self.scoring_rules["engagement"]["delayed"]

            # Create lead record
            lead = Lead(
                email=normalized_email,
                source=source,
                content_id=content_id,
                lead_score=lead_score,
                utm_source=utm_params.get("utm_source") if utm_params else None,
                utm_medium=utm_params.get("utm_medium") if utm_params else None,
                utm_campaign=utm_params.get("utm_campaign") if utm_params else None,
            )
            self.db.add(lead)

            # Record revenue event
            event = RevenueEvent(
                event_type="lead_capture",
                amount=0.00,  # No immediate revenue from lead capture
                customer_email=normalized_email,
                content_id=content_id,
                event_metadata=json.dumps(
                    {
                        "source": source,
                        "lead_score": lead_score,
                        "utm_params": utm_params,
                        "additional": metadata,
                    }
                ),
            )
            self.db.add(event)

            self.db.commit()

            # Trigger welcome sequence
            self._trigger_welcome_sequence(lead.id)

            # Record metrics - disabled for now
            # record_business_metric("content_quality", value=1.0)

            return {
                "success": True,
                "lead_id": lead.id,
                "lead_score": lead_score,
                "sequence_triggered": "welcome",
            }

        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def _trigger_welcome_sequence(self, lead_id: int):
        """Trigger automated email nurturing sequence"""
        # In a real implementation, this would integrate with an email service
        # For now, we'll just log the sequence trigger
        print(f"Welcome sequence triggered for lead {lead_id}")

        # Record metric - disabled for now
        # record_business_metric("content_quality", value=1.0)

    def mark_conversion(self, email: str, conversion_value: float = 0.0) -> bool:
        """Mark a lead as converted to customer"""
        try:
            lead = self.db.query(Lead).filter_by(email=email).first()
            if not lead:
                return False

            lead.converted = True
            lead.conversion_date = datetime.utcnow()

            # Create or update customer record
            customer = self.db.query(Customer).filter_by(email=email).first()
            if not customer:
                customer = Customer(
                    email=email,
                    acquisition_source=lead.source,
                    lifetime_value=conversion_value,
                )
                self.db.add(customer)
            else:
                customer.lifetime_value += conversion_value

            # Record revenue event
            event = RevenueEvent(
                event_type="lead_conversion",
                amount=conversion_value,
                customer_email=email,
                content_id=lead.content_id,
                event_metadata=json.dumps(
                    {
                        "lead_id": lead.id,
                        "days_to_convert": (datetime.utcnow() - lead.captured_at).days,
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
            print(f"Error marking conversion: {e}")
            return False

    def get_lead_analytics(self, days: int = 30) -> Dict:
        """Get lead capture analytics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Total leads
        total_leads = (
            self.db.query(func.count(Lead.id))
            .filter(Lead.captured_at >= cutoff_date)
            .scalar()
        )

        # Leads by source
        leads_by_source = (
            self.db.query(Lead.source, func.count(Lead.id).label("count"))
            .filter(Lead.captured_at >= cutoff_date)
            .group_by(Lead.source)
            .all()
        )

        # Conversion stats
        converted_leads = (
            self.db.query(func.count(Lead.id))
            .filter(Lead.captured_at >= cutoff_date, Lead.converted)
            .scalar()
        )

        # Average lead score
        avg_score = (
            self.db.query(func.avg(Lead.lead_score))
            .filter(Lead.captured_at >= cutoff_date)
            .scalar()
            or 0
        )

        # Best performing content
        top_content = (
            self.db.query(Lead.content_id, func.count(Lead.id).label("lead_count"))
            .filter(Lead.captured_at >= cutoff_date, Lead.content_id.isnot(None))
            .group_by(Lead.content_id)
            .order_by(func.count(Lead.id).desc())
            .limit(5)
            .all()
        )

        return {
            "period_days": days,
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "conversion_rate": (
                (converted_leads / total_leads * 100) if total_leads > 0 else 0
            ),
            "average_lead_score": float(avg_score),
            "leads_by_source": {source: count for source, count in leads_by_source},
            "top_content_ids": [
                {"content_id": content_id, "leads": count}
                for content_id, count in top_content
            ],
        }

    def export_leads(self, converted_only: bool = False) -> List[Dict]:
        """Export lead data for CRM integration"""
        query = self.db.query(Lead)
        if converted_only:
            query = query.filter_by(converted=True)

        leads = query.order_by(Lead.captured_at.desc()).all()

        return [
            {
                "email": lead.email,
                "source": lead.source,
                "captured_at": lead.captured_at.isoformat(),
                "converted": lead.converted,
                "lead_score": lead.lead_score,
                "utm_source": lead.utm_source,
                "utm_medium": lead.utm_medium,
                "utm_campaign": lead.utm_campaign,
            }
            for lead in leads
        ]

    def add_lead_tag(self, email: str, tag: str) -> bool:
        """Add a tag to a lead for segmentation"""
        # This would integrate with a CRM or email service
        # For now, we'll just track it in metadata
        try:
            lead = self.db.query(Lead).filter_by(email=email).first()
            if lead:
                # In a real implementation, we'd have a separate tags table
                print(f"Tag '{tag}' added to lead {email}")
                return True
        except Exception as e:
            print(f"Error adding tag: {e}")

        return False
