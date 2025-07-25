import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

import stripe
from sqlalchemy.orm import Session

from services.common.metrics import update_revenue_projection
from services.revenue.db.models import Customer, RevenueEvent, Subscription


class RevenueManager:
    """Manages Stripe payments and subscription lifecycle"""

    def __init__(self, db: Session):
        self.db = db
        # Initialize Stripe with API key from environment
        stripe.api_key = os.getenv("STRIPE_API_KEY", "sk_test_placeholder")

        # Subscription tiers configuration
        self.subscription_tiers = {
            "basic": {
                "price": 29,
                "price_id": os.getenv("STRIPE_PRICE_BASIC", "price_basic_test"),
                "features": ["basic_analytics", "5_personas", "100_posts_month"],
            },
            "pro": {
                "price": 97,
                "price_id": os.getenv("STRIPE_PRICE_PRO", "price_pro_test"),
                "features": [
                    "advanced_analytics",
                    "custom_personas",
                    "unlimited_posts",
                    "priority_support",
                ],
            },
            "enterprise": {
                "price": 297,
                "price_id": os.getenv(
                    "STRIPE_PRICE_ENTERPRISE", "price_enterprise_test"
                ),
                "features": [
                    "white_label",
                    "api_access",
                    "dedicated_support",
                    "custom_integrations",
                ],
            },
        }

    def create_or_get_customer(
        self, email: str, name: Optional[str] = None
    ) -> Customer:
        """Create or retrieve a customer record"""
        # Check if customer exists
        customer = self.db.query(Customer).filter_by(email=email).first()

        if not customer:
            # Create Stripe customer
            try:
                stripe_customer = stripe.Customer.create(
                    email=email, name=name or "", metadata={"source": "threads_agent"}
                )

                # Create local customer record
                customer = Customer(  # type: ignore[call-arg]
                    email=email,
                    stripe_customer_id=stripe_customer.id,
                    name=name,
                    acquisition_source="organic",
                )
                self.db.add(customer)
                self.db.commit()

                # Record metrics
                # TODO: Add proper customer metrics
                # record_business_metric("customers_total", 1.0)

            except Exception as e:  # stripe.error.StripeError
                print(f"Stripe error creating customer: {e}")
                raise

        return customer

    def create_subscription(
        self, email: str, tier: str, payment_method_id: str, trial_days: int = 0
    ) -> Dict[str, Any]:
        """Create a new subscription"""
        if tier not in self.subscription_tiers:
            raise ValueError(f"Invalid subscription tier: {tier}")

        try:
            # Get or create customer
            customer = self.create_or_get_customer(email)

            # Attach payment method to customer
            stripe.PaymentMethod.attach(
                payment_method_id, customer=customer.stripe_customer_id or ""
            )

            # Set as default payment method
            stripe.Customer.modify(
                customer.stripe_customer_id or "",
                invoice_settings={"default_payment_method": payment_method_id},
            )

            # Create subscription
            tier_config = self.subscription_tiers[tier]
            subscription_params = {
                "customer": customer.stripe_customer_id,
                "items": [{"price": tier_config["price_id"]}],
                "metadata": {"tier": tier, "source": "threads_agent"},
            }

            if trial_days > 0:
                subscription_params["trial_period_days"] = trial_days  # type: ignore[assignment]

            stripe_subscription = stripe.Subscription.create(**subscription_params)  # type: ignore[arg-type]

            # Store subscription in database
            subscription = Subscription(  # type: ignore[call-arg]
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=customer.stripe_customer_id,
                customer_email=email,
                tier=tier,
                status=stripe_subscription.status,
                monthly_amount=Decimal(str(tier_config["price"])),
            )
            self.db.add(subscription)

            # Record revenue event
            event = RevenueEvent(  # type: ignore[call-arg]
                event_type="subscription",
                amount=Decimal(str(tier_config["price"])),
                customer_email=email,
                event_metadata=json.dumps(
                    {"tier": tier, "subscription_id": stripe_subscription.id}
                ),
            )
            self.db.add(event)

            # Update customer lifetime value
            customer.lifetime_value += Decimal(str(tier_config["price"]))
            customer.last_purchase_date = datetime.utcnow()

            self.db.commit()

            # Record metrics
            # TODO: Add proper subscription metrics
            # record_business_metric("subscriptions_created_total", 1.0)
            # record_business_metric(f"subscriptions_{tier}_total", 1.0)
            # record_business_metric("mrr_usd", float(tier_config["price"]))
            update_revenue_projection("subscription", float(tier_config["price"]))  # type: ignore[arg-type]

            return {
                "success": True,
                "subscription_id": subscription.id,
                "stripe_subscription_id": stripe_subscription.id,
                "status": stripe_subscription.status,
                "tier": tier,
                "features": tier_config["features"],
            }

        except Exception as e:  # stripe.error.StripeError
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def cancel_subscription(
        self, subscription_id: int, immediate: bool = False
    ) -> Dict[str, Any]:
        """Cancel a subscription"""
        try:
            # Get subscription from database
            subscription = (
                self.db.query(Subscription).filter_by(id=subscription_id).first()
            )
            if not subscription:
                return {"success": False, "error": "Subscription not found"}

            # Cancel in Stripe
            if immediate:
                stripe.Subscription.delete(subscription.stripe_subscription_id)  # type: ignore[arg-type]
            else:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id, cancel_at_period_end=True
                )

            # Update local record
            subscription.status = "canceled" if immediate else "canceling"
            subscription.canceled_at = datetime.utcnow()

            self.db.commit()

            # Record metrics
            # TODO: Add proper cancellation metrics
            # record_business_metric("subscriptions_canceled_total", 1.0)
            # record_business_metric("mrr_usd", -float(subscription.monthly_amount))

            return {"success": True, "status": subscription.status}

        except Exception as e:  # stripe.error.StripeError
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle Stripe webhooks"""
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(payload, signature, endpoint_secret)  # type: ignore[no-untyped-call]

            # Handle different event types
            if event.type == "invoice.payment_succeeded":
                # Recurring payment successful
                invoice = event.data.object
                subscription_id = invoice.subscription
                amount = invoice.amount_paid / 100  # Convert from cents

                # Record revenue event
                revenue_event = RevenueEvent(  # type: ignore[call-arg]
                    event_type="subscription_payment",
                    amount=Decimal(str(amount)),
                    customer_email=invoice.customer_email,
                    event_metadata=json.dumps(
                        {"invoice_id": invoice.id, "subscription_id": subscription_id}
                    ),
                )
                self.db.add(revenue_event)

                # Update customer lifetime value
                customer = (
                    self.db.query(Customer)
                    .filter_by(stripe_customer_id=invoice.customer)
                    .first()
                )
                if customer:
                    customer.lifetime_value += Decimal(str(amount))
                    customer.last_purchase_date = datetime.utcnow()

                self.db.commit()

                # Record metrics
                # TODO: Add proper revenue metrics
                # record_business_metric("revenue_total_usd", amount)
                update_revenue_projection("subscription_payment", amount)

            elif event.type == "customer.subscription.deleted":
                # Subscription canceled
                subscription = event.data.object
                local_sub = (
                    self.db.query(Subscription)
                    .filter_by(stripe_subscription_id=subscription.id)
                    .first()
                )

                if local_sub:
                    local_sub.status = "canceled"
                    local_sub.canceled_at = datetime.utcnow()
                    self.db.commit()

                    # Record metrics
                    # TODO: Add proper MRR metrics
                    # record_business_metric("mrr_usd", -float(local_sub.monthly_amount))

            elif event.type == "customer.subscription.updated":
                # Subscription updated (upgrade/downgrade)
                subscription = event.data.object
                local_sub = (
                    self.db.query(Subscription)
                    .filter_by(stripe_subscription_id=subscription.id)
                    .first()
                )

                if local_sub:
                    # Determine new tier from price
                    for tier, config in self.subscription_tiers.items():
                        if subscription.items.data[0].price.id == config["price_id"]:
                            # old_amount = float(local_sub.monthly_amount)
                            new_amount = float(config["price"])  # type: ignore[arg-type]

                            local_sub.tier = tier
                            local_sub.monthly_amount = Decimal(str(new_amount))
                            local_sub.status = subscription.status

                            self.db.commit()

                            # Record metrics
                            # TODO: Add proper MRR change metrics
                            # old_amount = float(local_sub.monthly_amount)
                            # mrr_change = new_amount - old_amount
                            # record_business_metric("mrr_usd", mrr_change)

                            # if mrr_change > 0:
                            #     record_business_metric("upgrades_total", 1.0)
                            # else:
                            #     record_business_metric("downgrades_total", 1.0)

                            break

            return {"success": True, "event_type": event.type}

        except Exception:  # stripe.error.SignatureVerificationError
            return {"success": False, "error": "Invalid signature"}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def get_subscription_status(self, subscription_id: int) -> Optional[Dict[str, Any]]:
        """Get current subscription status"""
        subscription = self.db.query(Subscription).filter_by(id=subscription_id).first()

        if subscription:
            return {
                "id": subscription.id,
                "tier": subscription.tier,
                "status": subscription.status,
                "monthly_amount": float(subscription.monthly_amount),
                "created_at": subscription.created_at.isoformat(),
                "features": self.subscription_tiers[subscription.tier]["features"],
            }

        return None

    def calculate_mrr(self) -> float:
        """Calculate current Monthly Recurring Revenue"""
        active_subscriptions = (
            self.db.query(Subscription).filter_by(status="active").all()
        )

        mrr = sum(float(sub.monthly_amount) for sub in active_subscriptions)

        # Update metric
        # TODO: Add proper MRR current metric
        # record_business_metric("mrr_current_usd", mrr)

        return mrr
