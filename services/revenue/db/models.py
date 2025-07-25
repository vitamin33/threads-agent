from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class AffiliateLink(Base):
    __tablename__ = "affiliate_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    link_url: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    merchant: Mapped[str] = mapped_column(String(100), nullable=False)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    conversion_count: Mapped[int] = mapped_column(Integer, default=0)
    revenue_generated: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_affiliate_links_content_id", "content_id"),
        Index("idx_affiliate_links_category", "category"),
    )


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    source: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'organic', 'affiliate', 'direct'
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    content_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    converted: Mapped[bool] = mapped_column(Boolean, default=False)
    conversion_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    lead_score: Mapped[int] = mapped_column(Integer, default=0)
    utm_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_leads_email", "email"),
        Index("idx_leads_source", "source"),
        Index("idx_leads_converted", "converted"),
    )


class RevenueEvent(Base):
    __tablename__ = "revenue_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'affiliate_click', 'subscription', 'lead_capture'
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    event_metadata: Mapped[Optional[str]] = mapped_column(
        "metadata", Text, nullable=True
    )  # JSON string for additional data

    __table_args__ = (
        Index("idx_revenue_events_type", "event_type"),
        Index("idx_revenue_events_created_at", "created_at"),
        Index("idx_revenue_events_customer", "customer_email"),
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stripe_subscription_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    stripe_customer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    tier: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'basic', 'pro', 'enterprise'
    status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'active', 'canceled', 'past_due'
    monthly_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_subscriptions_customer", "customer_email"),
        Index("idx_subscriptions_status", "status"),
        Index("idx_subscriptions_tier", "tier"),
    )


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lifetime_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    acquisition_source: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    acquisition_date: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_purchase_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    __table_args__ = (
        Index("idx_customers_email", "email"),
        Index("idx_customers_stripe_id", "stripe_customer_id"),
    )


__all__ = ["Base", "Customer", "Lead", "AffiliateLink", "Subscription", "RevenueEvent"]
