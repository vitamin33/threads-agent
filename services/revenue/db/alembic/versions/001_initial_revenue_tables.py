"""Initial revenue tables

Revision ID: 001
Revises:
Create Date: 2024-01-22

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create affiliate_links table
    op.create_table(
        "affiliate_links",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("content_id", sa.BigInteger(), nullable=True),
        sa.Column("link_url", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("merchant", sa.String(length=100), nullable=False),
        sa.Column("click_count", sa.Integer(), nullable=True),
        sa.Column("conversion_count", sa.Integer(), nullable=True),
        sa.Column(
            "revenue_generated", sa.Numeric(precision=10, scale=2), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_affiliate_links_category", "affiliate_links", ["category"], unique=False
    )
    op.create_index(
        "idx_affiliate_links_content_id",
        "affiliate_links",
        ["content_id"],
        unique=False,
    )

    # Create leads table
    op.create_table(
        "leads",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=True),
        sa.Column("content_id", sa.BigInteger(), nullable=True),
        sa.Column("converted", sa.Boolean(), nullable=True),
        sa.Column("conversion_date", sa.DateTime(), nullable=True),
        sa.Column("lead_score", sa.Integer(), nullable=True),
        sa.Column("utm_source", sa.String(length=100), nullable=True),
        sa.Column("utm_medium", sa.String(length=100), nullable=True),
        sa.Column("utm_campaign", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_leads_converted", "leads", ["converted"], unique=False)
    op.create_index("idx_leads_email", "leads", ["email"], unique=False)
    op.create_index("idx_leads_source", "leads", ["source"], unique=False)

    # Create revenue_events table
    op.create_table(
        "revenue_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=True),
        sa.Column("content_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_revenue_events_created_at", "revenue_events", ["created_at"], unique=False
    )
    op.create_index(
        "idx_revenue_events_customer",
        "revenue_events",
        ["customer_email"],
        unique=False,
    )
    op.create_index(
        "idx_revenue_events_type", "revenue_events", ["event_type"], unique=False
    )

    # Create subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("stripe_subscription_id", sa.String(length=255), nullable=False),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=False),
        sa.Column("tier", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("monthly_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("canceled_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_subscription_id"),
    )
    op.create_index(
        "idx_subscriptions_customer", "subscriptions", ["customer_email"], unique=False
    )
    op.create_index(
        "idx_subscriptions_status", "subscriptions", ["status"], unique=False
    )
    op.create_index("idx_subscriptions_tier", "subscriptions", ["tier"], unique=False)

    # Create customers table
    op.create_table(
        "customers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("lifetime_value", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("acquisition_source", sa.String(length=100), nullable=True),
        sa.Column("acquisition_date", sa.DateTime(), nullable=True),
        sa.Column("last_purchase_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("stripe_customer_id"),
    )
    op.create_index("idx_customers_email", "customers", ["email"], unique=False)
    op.create_index(
        "idx_customers_stripe_id", "customers", ["stripe_customer_id"], unique=False
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index("idx_customers_stripe_id", table_name="customers")
    op.drop_index("idx_customers_email", table_name="customers")
    op.drop_table("customers")

    op.drop_index("idx_subscriptions_tier", table_name="subscriptions")
    op.drop_index("idx_subscriptions_status", table_name="subscriptions")
    op.drop_index("idx_subscriptions_customer", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index("idx_revenue_events_type", table_name="revenue_events")
    op.drop_index("idx_revenue_events_customer", table_name="revenue_events")
    op.drop_index("idx_revenue_events_created_at", table_name="revenue_events")
    op.drop_table("revenue_events")

    op.drop_index("idx_leads_source", table_name="leads")
    op.drop_index("idx_leads_email", table_name="leads")
    op.drop_index("idx_leads_converted", table_name="leads")
    op.drop_table("leads")

    op.drop_index("idx_affiliate_links_content_id", table_name="affiliate_links")
    op.drop_index("idx_affiliate_links_category", table_name="affiliate_links")
    op.drop_table("affiliate_links")
