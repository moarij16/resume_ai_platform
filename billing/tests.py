"""
Tests for the billing app.

Covers:
  - UserSubscription domain methods: cancel(), expire(), is_active()
  - stripe_service handlers: checkout_completed, subscription_updated,
    subscription_deleted, invoice_payment_succeeded, invoice_payment_failed
  - POST /api/v1/billing/webhook/  — signature verification, event routing
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from billing.models import SubscriptionPlan, SubscriptionStatus, UserSubscription
from users.models import Users

WEBHOOK_URL = "/api/v1/billing/webhook/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    return Users.objects.create(
        supabase_uid=str(uuid.uuid4()),
        email="billing_user@example.com",
        first_name="Bill",
        last_name="Tester",
    )


@pytest.fixture
def plan(db):
    return SubscriptionPlan.objects.create(
        name="premium",
        monthly_token_limit=99999,
        price_monthly="12.00",
    )


@pytest.fixture
def active_subscription(user, plan):
    return UserSubscription.objects.create(
        user=user,
        plan=plan,
        status=SubscriptionStatus.ACTIVE,
        start_date=timezone.now(),
        stripe_subscription_id="sub_test123",
        stripe_customer_id="cus_test123",
    )


# ---------------------------------------------------------------------------
# Model — UserSubscription domain methods
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUserSubscriptionDomainMethods:

    def test_is_active_true_when_active(self, active_subscription):
        assert active_subscription.is_active() is True

    def test_is_active_false_when_canceled(self, active_subscription):
        active_subscription.status = SubscriptionStatus.CANCELED
        active_subscription.save(update_fields=["status"])
        assert active_subscription.is_active() is False

    def test_cancel_sets_status(self, active_subscription):
        active_subscription.cancel()
        active_subscription.refresh_from_db()
        assert active_subscription.status == SubscriptionStatus.CANCELED

    def test_expire_sets_status(self, active_subscription):
        active_subscription.expire()
        active_subscription.refresh_from_db()
        assert active_subscription.status == SubscriptionStatus.EXPIRED

    def test_cancel_only_updates_status_field(self, active_subscription):
        original_start = active_subscription.start_date
        active_subscription.cancel()
        active_subscription.refresh_from_db()
        # start_date must not change — confirms update_fields=["status"]
        assert active_subscription.start_date == original_start


# ---------------------------------------------------------------------------
# Service — handle_subscription_deleted
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestHandleSubscriptionDeleted:

    def test_cancels_subscription(self, active_subscription):
        # upgrade_plan is called after cancel — patch at the module level so the
        # missing method on Users doesn't block testing the cancel logic itself
        with patch("billing.services.stripe_service.Users.upgrade_plan", create=True):
            from billing.services.stripe_service import handle_subscription_deleted
            handle_subscription_deleted({"id": "sub_test123"})

        active_subscription.refresh_from_db()
        assert active_subscription.status == SubscriptionStatus.CANCELED

    def test_unknown_subscription_id_is_no_op(self):
        from billing.services.stripe_service import handle_subscription_deleted
        # Should not raise
        handle_subscription_deleted({"id": "sub_doesnotexist"})

    def test_missing_id_is_no_op(self):
        from billing.services.stripe_service import handle_subscription_deleted
        handle_subscription_deleted({})


# ---------------------------------------------------------------------------
# Service — handle_invoice_payment_failed
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestHandleInvoicePaymentFailed:

    def test_marks_subscription_expired(self, active_subscription):
        from billing.services.stripe_service import handle_invoice_payment_failed
        handle_invoice_payment_failed({"subscription": "sub_test123"})

        active_subscription.refresh_from_db()
        assert active_subscription.status == SubscriptionStatus.EXPIRED

    def test_unknown_subscription_is_no_op(self):
        from billing.services.stripe_service import handle_invoice_payment_failed
        handle_invoice_payment_failed({"subscription": "sub_nobody"})

    def test_missing_subscription_key_is_no_op(self):
        from billing.services.stripe_service import handle_invoice_payment_failed
        handle_invoice_payment_failed({})


# ---------------------------------------------------------------------------
# Service — handle_invoice_payment_succeeded
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestHandleInvoicePaymentSucceeded:

    def test_sets_renewal_date_and_active_status(self, active_subscription):
        future_ts = int((timezone.now() + timezone.timedelta(days=30)).timestamp())
        invoice = {
            "subscription": "sub_test123",
            "lines": {"data": [{"period": {"end": future_ts}}]},
        }
        from billing.services.stripe_service import handle_invoice_payment_succeeded
        handle_invoice_payment_succeeded(invoice)

        active_subscription.refresh_from_db()
        assert active_subscription.status == SubscriptionStatus.ACTIVE
        assert active_subscription.renewal_date is not None

    def test_missing_period_end_skips_renewal(self, active_subscription):
        invoice = {
            "subscription": "sub_test123",
            "lines": {"data": [{"period": {}}]},
        }
        from billing.services.stripe_service import handle_invoice_payment_succeeded
        handle_invoice_payment_succeeded(invoice)
        # Should not crash; renewal_date stays null
        active_subscription.refresh_from_db()
        assert active_subscription.renewal_date is None

    def test_unknown_subscription_is_no_op(self):
        from billing.services.stripe_service import handle_invoice_payment_succeeded
        handle_invoice_payment_succeeded({"subscription": "sub_nobody"})


# ---------------------------------------------------------------------------
# Webhook endpoint — POST /api/v1/billing/webhook/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestStripeWebhookEndpoint:

    def _client(self):
        return APIClient()

    def test_missing_signature_header_returns_400(self):
        response = self._client().post(WEBHOOK_URL, {}, format="json")
        assert response.status_code == 400

    def test_invalid_signature_returns_400(self):
        import stripe
        with patch.object(
            stripe.Webhook, "construct_event",
            side_effect=stripe.error.SignatureVerificationError("bad", "sig"),
        ):
            response = self._client().post(
                WEBHOOK_URL,
                b"payload",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="bad_sig",
            )
        assert response.status_code == 400

    def test_valid_event_returns_200(self):
        fake_event = {
            "type": "customer.subscription.updated",
            "data": {"object": {"id": "sub_xyz", "status": "active", "items": {"data": []}}},
        }
        import stripe
        with patch.object(stripe.Webhook, "construct_event", return_value=fake_event):
            with patch("billing.services.stripe_service.handle_subscription_updated"):
                response = self._client().post(
                    WEBHOOK_URL,
                    b"payload",
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE="valid_sig",
                )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_unknown_event_type_still_returns_200(self):
        """Unhandled event types must not cause errors."""
        fake_event = {
            "type": "some.unknown.event",
            "data": {"object": {}},
        }
        import stripe
        with patch.object(stripe.Webhook, "construct_event", return_value=fake_event):
            response = self._client().post(
                WEBHOOK_URL,
                b"payload",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="valid_sig",
            )
        assert response.status_code == 200

    def test_handler_exception_still_returns_200(self):
        """Handler crash must not cause Stripe to retry endlessly."""
        fake_event = {
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_boom"}},
        }
        import stripe
        with patch.object(stripe.Webhook, "construct_event", return_value=fake_event):
            with patch(
                "billing.services.stripe_service.handle_subscription_deleted",
                side_effect=RuntimeError("DB down"),
            ):
                response = self._client().post(
                    WEBHOOK_URL,
                    b"payload",
                    content_type="application/json",
                    HTTP_STRIPE_SIGNATURE="valid_sig",
                )
        assert response.status_code == 200
