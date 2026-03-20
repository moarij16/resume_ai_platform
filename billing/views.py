import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from billing.services.stripe_service import (
    handle_checkout_completed,
    handle_subscription_updated,
    handle_subscription_deleted,
    handle_invoice_payment_succeeded,
    handle_invoice_payment_failed,
)


# ── Stripe Webhook ────────────────────────────────────────────────────


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def stripe_webhook(request):
    """
    Public endpoint — Stripe calls this directly.
    Must verify signature to confirm request is from Stripe.
    Must return 200 quickly — do not do slow work here.
    """
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    if not sig_header:
        return Response(
            {"error": "Missing Stripe signature"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Verify the request came from Stripe
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        # Invalid payload
        return Response(
            {"error": "Invalid payload"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except stripe.error.SignatureVerificationError:
        # Invalid signature — not from Stripe
        return Response(
            {"error": "Invalid signature"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Route to correct handler
    event_type = event["type"]
    event_data = event["data"]["object"]

    handlers = {
        "checkout.session.completed": handle_checkout_completed,
        "customer.subscription.updated": handle_subscription_updated,
        "customer.subscription.deleted": handle_subscription_deleted,
        "invoice.payment_succeeded": handle_invoice_payment_succeeded,
        "invoice.payment_failed": handle_invoice_payment_failed,
    }

    handler = handlers.get(event_type)
    if handler:
        try:
            handler(event_data)
        except Exception as e:
            # Log but still return 200 — we don't want Stripe to retry
            # a bug in our code endlessly
            print(f"Webhook handler error for {event_type}: {e}")

    return Response({"status": "ok"}, status=status.HTTP_200_OK)


# ── Billing ViewSet ───────────────────────────────────────────────────


class BillingViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="status")
    def billing_status(self, request):
        return Response({"message": "billing status exists"})

    @action(detail=False, methods=["post"], url_path="subscribe")
    def subscribe(self, request):
        return Response({"message": "subscribe exists"})

    @action(detail=False, methods=["post"], url_path="unsubscribe")
    def unsubscribe(self, request):
        return Response({"message": "unsubscribe exists"})
