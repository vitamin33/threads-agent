from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy import Integer, and_, func
from sqlalchemy.orm import Session

from services.revenue.db.models import (
    AffiliateLink,
    Customer,
    Lead,
    RevenueEvent,
    Subscription,
)


class RevenueAnalytics:
    """Comprehensive revenue analytics and reporting"""

    def __init__(self, db: Session):
        self.db = db

    def get_revenue_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive revenue summary for the specified period"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Total revenue by type
        revenue_by_type = (
            self.db.query(
                RevenueEvent.event_type, func.sum(RevenueEvent.amount).label("total")
            )
            .filter(RevenueEvent.created_at >= cutoff_date)
            .group_by(RevenueEvent.event_type)
            .all()
        )

        # Convert to dict
        revenue_dict = {
            event_type: float(total or 0) for event_type, total in revenue_by_type
        }

        # Calculate total revenue
        total_revenue = sum(revenue_dict.values())

        # Get MRR (Monthly Recurring Revenue)
        active_subscriptions = (
            self.db.query(Subscription).filter_by(status="active").all()
        )
        current_mrr = sum(float(sub.monthly_amount) for sub in active_subscriptions)

        # Get customer metrics
        total_customers = self.db.query(func.count(Customer.id)).scalar()
        new_customers = (
            self.db.query(func.count(Customer.id))
            .filter(Customer.acquisition_date >= cutoff_date)
            .scalar()
        )

        # Average revenue per user (ARPU)
        arpu = total_revenue / total_customers if total_customers > 0 else 0

        # Churn rate (subscriptions canceled in period / total at start)
        canceled_subs = (
            self.db.query(func.count(Subscription.id))
            .filter(
                and_(
                    Subscription.canceled_at >= cutoff_date,
                    Subscription.status.in_(["canceled", "canceling"]),
                )
            )
            .scalar()
        )

        total_subs_start = (
            self.db.query(func.count(Subscription.id))
            .filter(Subscription.created_at < cutoff_date)
            .scalar()
        )

        churn_rate = (
            (canceled_subs / total_subs_start * 100) if total_subs_start > 0 else 0
        )

        return {
            "period_days": days,
            "total_revenue": total_revenue,
            "revenue_by_type": revenue_dict,
            "current_mrr": current_mrr,
            "projected_annual_revenue": current_mrr * 12,
            "total_customers": total_customers,
            "new_customers": new_customers,
            "arpu": round(arpu, 2),
            "churn_rate_percent": round(churn_rate, 2),
            "growth_rate_percent": round(
                (new_customers / total_customers * 100) if total_customers > 0 else 0, 2
            ),
        }

    def get_affiliate_performance(self, days: int = 30) -> Dict[str, Any]:
        """Get affiliate program performance metrics"""
        # Overall affiliate metrics
        total_clicks = self.db.query(func.sum(AffiliateLink.click_count)).scalar() or 0
        total_conversions = (
            self.db.query(func.sum(AffiliateLink.conversion_count)).scalar() or 0
        )
        total_affiliate_revenue = self.db.query(
            func.sum(AffiliateLink.revenue_generated)
        ).scalar() or Decimal("0")

        # Performance by category
        category_performance = (
            self.db.query(
                AffiliateLink.category,
                func.sum(AffiliateLink.click_count).label("clicks"),
                func.sum(AffiliateLink.conversion_count).label("conversions"),
                func.sum(AffiliateLink.revenue_generated).label("revenue"),
            )
            .group_by(AffiliateLink.category)
            .all()
        )

        # Top performing merchants
        top_merchants = (
            self.db.query(
                AffiliateLink.merchant,
                func.sum(AffiliateLink.revenue_generated).label("revenue"),
                func.sum(AffiliateLink.click_count).label("clicks"),
                func.sum(AffiliateLink.conversion_count).label("conversions"),
            )
            .group_by(AffiliateLink.merchant)
            .order_by(func.sum(AffiliateLink.revenue_generated).desc())
            .limit(10)
            .all()
        )

        # Calculate overall conversion rate
        overall_conversion_rate = (
            (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        )

        return {
            "period_days": days,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_revenue": float(total_affiliate_revenue),
            "overall_conversion_rate": round(overall_conversion_rate, 2),
            "average_commission": (
                float(total_affiliate_revenue / total_conversions)
                if total_conversions > 0
                else 0
            ),
            "category_performance": [
                {
                    "category": cat,
                    "clicks": clicks,
                    "conversions": conversions,
                    "revenue": float(revenue),
                    "conversion_rate": round(
                        (conversions / clicks * 100) if clicks > 0 else 0, 2
                    ),
                }
                for cat, clicks, conversions, revenue in category_performance
            ],
            "top_merchants": [
                {
                    "merchant": merchant,
                    "revenue": float(revenue),
                    "clicks": clicks,
                    "conversions": conversions,
                    "conversion_rate": round(
                        (conversions / clicks * 100) if clicks > 0 else 0, 2
                    ),
                }
                for merchant, revenue, clicks, conversions in top_merchants
            ],
        }

    def get_lead_funnel_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get lead funnel conversion metrics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Funnel stages
        total_leads = (
            self.db.query(func.count(Lead.id))
            .filter(Lead.captured_at >= cutoff_date)
            .scalar()
        )

        qualified_leads = (
            self.db.query(func.count(Lead.id))
            .filter(
                and_(
                    Lead.captured_at >= cutoff_date,
                    Lead.lead_score >= 30,  # Arbitrary threshold for "qualified"
                )
            )
            .scalar()
        )

        converted_leads = (
            self.db.query(func.count(Lead.id))
            .filter(and_(Lead.captured_at >= cutoff_date, Lead.converted))
            .scalar()
        )

        # Lead sources performance
        lead_sources = (
            self.db.query(
                Lead.source,
                func.count(Lead.id).label("count"),
                func.avg(Lead.lead_score).label("avg_score"),
                func.sum(Lead.converted.cast(Integer)).label("conversions"),
            )
            .filter(Lead.captured_at >= cutoff_date)
            .group_by(Lead.source)
            .all()
        )

        # Time to conversion
        converted_leads_data = (
            self.db.query(Lead.captured_at, Lead.conversion_date)
            .filter(
                and_(
                    Lead.captured_at >= cutoff_date,
                    Lead.converted,
                    Lead.conversion_date.isnot(None),
                )
            )
            .all()
        )

        avg_days_to_convert = 0
        if converted_leads_data:
            total_days = sum(
                (conv_date - cap_date).days
                for cap_date, conv_date in converted_leads_data
            )
            avg_days_to_convert = total_days / len(converted_leads_data)

        return {
            "period_days": days,
            "funnel": {
                "total_leads": total_leads,
                "qualified_leads": qualified_leads,
                "converted_leads": converted_leads,
                "qualification_rate": round(
                    (qualified_leads / total_leads * 100) if total_leads > 0 else 0, 2
                ),
                "conversion_rate": round(
                    (converted_leads / total_leads * 100) if total_leads > 0 else 0, 2
                ),
            },
            "avg_days_to_convert": round(avg_days_to_convert, 1),
            "source_performance": [
                {
                    "source": source,
                    "leads": count,
                    "avg_score": round(float(avg_score or 0), 1),
                    "conversions": conversions or 0,
                    "conversion_rate": round(
                        (conversions / count * 100) if count > 0 else 0, 2
                    ),
                }
                for source, count, avg_score, conversions in lead_sources
            ],
        }

    def get_subscription_metrics(self) -> Dict[str, Any]:
        """Get detailed subscription metrics"""
        # Subscription distribution by tier
        tier_distribution = (
            self.db.query(
                Subscription.tier,
                func.count(Subscription.id).label("count"),
                func.sum(Subscription.monthly_amount).label("mrr"),
            )
            .filter_by(status="active")
            .group_by(Subscription.tier)
            .all()
        )

        # Lifetime value by tier
        ltv_by_tier = {}
        for tier, _, _ in tier_distribution:
            # Calculate average customer lifetime (inverse of churn rate)
            tier_churn = (
                self.db.query(func.count(Subscription.id))
                .filter(
                    and_(
                        Subscription.tier == tier,
                        Subscription.status.in_(["canceled", "canceling"]),
                    )
                )
                .scalar()
            )

            tier_total = (
                self.db.query(func.count(Subscription.id)).filter_by(tier=tier).scalar()
            )

            if tier_total > 0:
                monthly_churn_rate = tier_churn / tier_total
                if monthly_churn_rate > 0:
                    avg_lifetime_months = 1 / monthly_churn_rate
                else:
                    avg_lifetime_months = 24  # Default to 2 years if no churn

                tier_mrr = next(
                    (float(mrr) for t, _, mrr in tier_distribution if t == tier), 0
                )
                tier_count = next(
                    (count for t, count, _ in tier_distribution if t == tier), 0
                )

                if tier_count > 0:
                    avg_monthly_value = tier_mrr / tier_count
                    ltv_by_tier[tier] = round(
                        avg_monthly_value * avg_lifetime_months, 2
                    )

        # Growth metrics
        new_subs_30d = (
            self.db.query(func.count(Subscription.id))
            .filter(
                and_(
                    Subscription.created_at >= datetime.utcnow() - timedelta(days=30),
                    Subscription.status == "active",
                )
            )
            .scalar()
        )

        canceled_subs_30d = (
            self.db.query(func.count(Subscription.id))
            .filter(Subscription.canceled_at >= datetime.utcnow() - timedelta(days=30))
            .scalar()
        )

        return {
            "tier_distribution": [
                {
                    "tier": tier,
                    "active_subscriptions": count,
                    "mrr": float(mrr),
                    "ltv": ltv_by_tier.get(tier, 0),
                }
                for tier, count, mrr in tier_distribution
            ],
            "total_mrr": sum(float(mrr) for _, _, mrr in tier_distribution),
            "new_subscriptions_30d": new_subs_30d,
            "canceled_subscriptions_30d": canceled_subs_30d,
            "net_growth_30d": new_subs_30d - canceled_subs_30d,
        }

    def get_revenue_forecast(self, months: int = 12) -> List[Dict[str, Any]]:
        """Generate revenue forecast based on current trends"""
        # Get current MRR
        current_mrr = self.db.query(func.sum(Subscription.monthly_amount)).filter_by(
            status="active"
        ).scalar() or Decimal("0")

        # Calculate growth rate from last 3 months
        growth_rates = []
        for i in range(1, 4):
            start_date = datetime.utcnow() - timedelta(days=30 * i)
            end_date = datetime.utcnow() - timedelta(days=30 * (i - 1))

            period_revenue = self.db.query(func.sum(RevenueEvent.amount)).filter(
                and_(
                    RevenueEvent.created_at >= start_date,
                    RevenueEvent.created_at < end_date,
                    RevenueEvent.event_type.in_(
                        ["subscription", "subscription_payment"]
                    ),
                )
            ).scalar() or Decimal("0")

            if i < 3:
                prev_period_revenue = self.db.query(
                    func.sum(RevenueEvent.amount)
                ).filter(
                    and_(
                        RevenueEvent.created_at >= start_date - timedelta(days=30),
                        RevenueEvent.created_at < start_date,
                        RevenueEvent.event_type.in_(
                            ["subscription", "subscription_payment"]
                        ),
                    )
                ).scalar() or Decimal("0")

                if prev_period_revenue > 0:
                    growth_rate = float(
                        (period_revenue - prev_period_revenue) / prev_period_revenue
                    )
                    growth_rates.append(growth_rate)

        # Use average growth rate or conservative 5% if no data
        avg_growth_rate = (
            sum(growth_rates) / len(growth_rates) if growth_rates else 0.05
        )

        # Generate forecast
        forecast: List[Dict[str, Any]] = []
        projected_mrr = float(current_mrr)

        for month in range(1, months + 1):
            projected_mrr *= 1 + avg_growth_rate

            # Add one-time revenue estimate (affiliate + one-time purchases)
            one_time_estimate = (
                projected_mrr * 0.2
            )  # Assume 20% additional from non-recurring

            forecast.append(
                {
                    "month": month,
                    "projected_mrr": round(projected_mrr, 2),
                    "projected_total_revenue": round(
                        projected_mrr + one_time_estimate, 2
                    ),
                    "cumulative_revenue": round(
                        sum(f["projected_total_revenue"] for f in forecast), 2
                    ),
                }
            )

        return forecast
