import datetime
import stripe
from django.conf import settings
from django.utils import timezone
from dateutil import parser as date_parser
from users.models import Users
from billing.models import UserSubscription, SubscriptionPlan, SubscriptionStatus

stripe.api_key = settings.STRIPE_SECRET_KEY


# ── Price ID → Plan name mapping ─────────────────────────────────────

PRICE_TO_PLAN = {
    settings.STRIPE_PRO_PRICE_ID: "premium",
    settings.STRIPE_CAREER_PRICE_ID: "career",
}


# ── Checkout completed ────────────────────────────────────────────────


def handle_checkout_completed(session: dict) -> None:
    """
    Fired when user completes checkout.
    Creates UserSubscription and upgrades UserProfile plan.
    """
    customer_email = session.get("customer_email")
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    price_id = _get_price_id_from_session(session)

    if not customer_email or not subscription_id:
        return

    try:
        user = Users.objects.get(email=customer_email)
    except Users.DoesNotExist:
        return

    plan_name = PRICE_TO_PLAN.get(price_id, "premium")

    # Get or create subscription plan record
    plan, _ = SubscriptionPlan.objects.get_or_create(
        name=plan_name,
        defaults={
            "monthly_token_limit": 99999,
            "price_monthly": 12.00 if plan_name == "premium" else 24.00,
        },
    )

    # Create subscription record
    UserSubscription.objects.update_or_create(
        user=user,
        defaults={
            "plan": plan,
            "status": SubscriptionStatus.ACTIVE,
            "start_date": timezone.now(),
            "stripe_subscription_id": subscription_id,
            "stripe_customer_id": customer_id,
        },
    )


# ── Subscription updated ──────────────────────────────────────────────


def handle_subscription_updated(subscription: dict) -> None:
    """
    Fired when plan changes or subscription is modified.
    """
    subscription_id = subscription.get("id")
    status = subscription.get("status")
    price_id = _get_price_id_from_subscription(subscription)

    try:
        user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription_id)
    except UserSubscription.DoesNotExist:
        return

    plan_name = PRICE_TO_PLAN.get(price_id, "premium")

    # Update plan if changed
    plan, _ = SubscriptionPlan.objects.get_or_create(
        name=plan_name,
        defaults={
            "monthly_token_limit": 99999,
            "price_monthly": 12.00 if plan_name == "premium" else 24.00,
        },
    )
    user_sub.plan = plan

    # Update status
    if status == "active":
        user_sub.status = SubscriptionStatus.ACTIVE
    elif status == "canceled":
        user_sub.status = SubscriptionStatus.CANCELED
    elif status == "past_due":
        user_sub.status = SubscriptionStatus.EXPIRED

    user_sub.save(update_fields=["plan", "status"])


# ── Subscription deleted ──────────────────────────────────────────────


def handle_subscription_deleted(subscription: dict) -> None:
    """
    Fired when subscription is fully cancelled.
    Downgrades user to free plan.
    """
    subscription_id = subscription.get("id")

    try:
        user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription_id)
    except UserSubscription.DoesNotExist:
        return

    user_sub.cancel()
    user_sub.user.upgrade_plan("free")


# ── Invoice payment succeeded ─────────────────────────────────────────


def handle_invoice_payment_succeeded(invoice: dict) -> None:
    """
    Fired on successful renewal payment.
    Extends subscription renewal date.
    """
    subscription_id = invoice.get("subscription")
    period_end = (
        invoice.get("lines", {}).get("data", [{}])[0].get("period", {}).get("end")
    )

    if not subscription_id:
        return

    try:
        user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription_id)
    except UserSubscription.DoesNotExist:
        return

    if period_end:
        user_sub.renewal_date = datetime.datetime.fromtimestamp(
            period_end, tz=datetime.timezone.utc
        )
        user_sub.status = SubscriptionStatus.ACTIVE
        user_sub.save(update_fields=["renewal_date", "status"])


# ── Invoice payment failed ────────────────────────────────────────────


def handle_invoice_payment_failed(invoice: dict) -> None:
    """
    Fired when renewal payment fails.
    Mark subscription as past due — don't immediately downgrade,
    Stripe will retry and send subscription.deleted if it keeps failing.
    """
    subscription_id = invoice.get("subscription")

    if not subscription_id:
        return

    try:
        user_sub = UserSubscription.objects.get(stripe_subscription_id=subscription_id)
    except UserSubscription.DoesNotExist:
        return

    user_sub.status = SubscriptionStatus.EXPIRED
    user_sub.save(update_fields=["status"])


# ── Private helpers ───────────────────────────────────────────────────


def _get_price_id_from_session(session: dict) -> str:
    """Extract price ID from checkout session."""
    try:
        line_items = stripe.checkout.Session.list_line_items(session["id"])
        return line_items["data"][0]["price"]["id"]
    except Exception:
        return ""


def _get_price_id_from_subscription(subscription: dict) -> str:
    """Extract price ID from subscription object."""
    try:
        return subscription["items"]["data"][0]["price"]["id"]
    except (KeyError, IndexError):
        return ""
