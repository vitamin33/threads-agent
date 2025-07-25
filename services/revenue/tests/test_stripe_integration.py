from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.revenue.db.models import Base, Customer, RevenueEvent, Subscription
from services.revenue.stripe_integration import RevenueManager


@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def revenue_manager(test_db):
    """Create RevenueManager with test database"""
    with patch.dict("os.environ", {"STRIPE_API_KEY": "sk_test_mock"}):
        return RevenueManager(test_db)


class TestRevenueManager:
    @patch("stripe.Customer.create")
    def test_create_customer(self, mock_stripe_create, revenue_manager, test_db):
        """Test customer creation"""
        # Mock Stripe response
        mock_stripe_create.return_value = Mock(
            id="cus_test123", email="test@example.com"
        )

        # Create customer
        customer = revenue_manager.create_or_get_customer(
            "test@example.com", "Test User"
        )

        assert customer is not None
        assert customer.email == "test@example.com"
        assert customer.stripe_customer_id == "cus_test123"
        assert customer.name == "Test User"

        # Verify it was saved
        db_customer = test_db.query(Customer).first()
        assert db_customer is not None
        assert db_customer.email == "test@example.com"

    def test_get_existing_customer(self, revenue_manager, test_db):
        """Test retrieving existing customer"""
        # Create existing customer
        existing = Customer(
            email="existing@example.com",
            stripe_customer_id="cus_existing",
            name="Existing User",
        )
        test_db.add(existing)
        test_db.commit()

        # Should return existing without calling Stripe
        with patch("stripe.Customer.create") as mock_create:
            customer = revenue_manager.create_or_get_customer("existing@example.com")
            mock_create.assert_not_called()

        assert customer.id == existing.id

    @patch("stripe.Subscription.create")
    @patch("stripe.PaymentMethod.attach")
    @patch("stripe.Customer.modify")
    def test_create_subscription(
        self,
        mock_customer_modify,
        mock_payment_attach,
        mock_sub_create,
        revenue_manager,
        test_db,
    ):
        """Test subscription creation"""
        # Create customer first
        customer = Customer(
            email="subscriber@example.com", stripe_customer_id="cus_subscriber"
        )
        test_db.add(customer)
        test_db.commit()

        # Mock Stripe responses
        mock_payment_attach.return_value = Mock(id="pm_test")
        mock_sub_create.return_value = Mock(
            id="sub_test123",
            status="active",
            items=Mock(data=[Mock(price=Mock(id="price_pro_test"))]),
        )

        # Create subscription
        result = revenue_manager.create_subscription(
            email="subscriber@example.com",
            tier="pro",
            payment_method_id="pm_test123",
            trial_days=7,
        )

        assert result["success"] is True
        assert result["tier"] == "pro"
        assert "features" in result

        # Verify subscription was saved
        subscription = test_db.query(Subscription).first()
        assert subscription is not None
        assert subscription.stripe_subscription_id == "sub_test123"
        assert subscription.tier == "pro"
        assert subscription.status == "active"
        assert float(subscription.monthly_amount) == 97.00

        # Verify revenue event
        event = test_db.query(RevenueEvent).first()
        assert event is not None
        assert event.event_type == "subscription"
        assert float(event.amount) == 97.00

    def test_create_subscription_invalid_tier(self, revenue_manager):
        """Test subscription with invalid tier"""
        with pytest.raises(ValueError, match="Invalid subscription tier"):
            revenue_manager.create_subscription(
                email="test@example.com",
                tier="invalid_tier",
                payment_method_id="pm_test",
            )

    @patch("stripe.Subscription.delete")
    def test_cancel_subscription_immediate(self, mock_delete, revenue_manager, test_db):
        """Test immediate subscription cancellation"""
        # Create subscription
        subscription = Subscription(
            stripe_subscription_id="sub_cancel",
            stripe_customer_id="cus_test",
            customer_email="cancel@example.com",
            tier="basic",
            status="active",
            monthly_amount=29.00,
        )
        test_db.add(subscription)
        test_db.commit()

        # Mock Stripe response
        mock_delete.return_value = Mock(status="canceled")

        # Cancel subscription
        result = revenue_manager.cancel_subscription(subscription.id, immediate=True)

        assert result["success"] is True
        assert result["status"] == "canceled"

        # Verify subscription was updated
        test_db.refresh(subscription)
        assert subscription.status == "canceled"
        assert subscription.canceled_at is not None

    def test_calculate_mrr(self, revenue_manager, test_db):
        """Test MRR calculation"""
        # Create subscriptions
        subscriptions = [
            ("active", 29.00),
            ("active", 97.00),
            ("active", 297.00),
            ("canceled", 29.00),  # Should not count
        ]

        for status, amount in subscriptions:
            sub = Subscription(
                stripe_subscription_id=f"sub_{status}_{amount}",
                stripe_customer_id="cus_test",
                customer_email=f"{status}@example.com",
                tier="basic",
                status=status,
                monthly_amount=amount,
            )
            test_db.add(sub)
        test_db.commit()

        # Calculate MRR
        mrr = revenue_manager.calculate_mrr()

        # Should only count active subscriptions
        assert mrr == 29.00 + 97.00 + 297.00

    @patch("stripe.Webhook.construct_event")
    def test_handle_webhook_payment_succeeded(
        self, mock_construct, revenue_manager, test_db
    ):
        """Test handling payment succeeded webhook"""
        # Create customer
        customer = Customer(
            email="webhook@example.com", stripe_customer_id="cus_webhook"
        )
        test_db.add(customer)
        test_db.commit()

        # Mock webhook event
        mock_event = Mock(
            type="invoice.payment_succeeded",
            data=Mock(
                object=Mock(
                    subscription="sub_test",
                    amount_paid=9700,  # $97.00 in cents
                    customer_email="webhook@example.com",
                    customer="cus_webhook",
                    id="inv_test",
                )
            ),
        )
        mock_construct.return_value = mock_event

        # Handle webhook
        result = revenue_manager.handle_webhook(b"payload", "sig_test")

        assert result["success"] is True
        assert result["event_type"] == "invoice.payment_succeeded"

        # Verify revenue event
        event = test_db.query(RevenueEvent).first()
        assert event is not None
        assert event.event_type == "subscription_payment"
        assert float(event.amount) == 97.00

        # Verify customer lifetime value updated
        test_db.refresh(customer)
        assert float(customer.lifetime_value) == 97.00

    def test_get_subscription_status(self, revenue_manager, test_db):
        """Test getting subscription status"""
        # Create subscription
        subscription = Subscription(
            stripe_subscription_id="sub_status",
            stripe_customer_id="cus_test",
            customer_email="status@example.com",
            tier="pro",
            status="active",
            monthly_amount=97.00,
        )
        test_db.add(subscription)
        test_db.commit()

        # Get status
        status = revenue_manager.get_subscription_status(subscription.id)

        assert status is not None
        assert status["tier"] == "pro"
        assert status["status"] == "active"
        assert status["monthly_amount"] == 97.00
        assert "features" in status

        # Non-existent subscription
        status = revenue_manager.get_subscription_status(999)
        assert status is None
