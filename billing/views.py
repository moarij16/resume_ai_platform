from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response


class BillingViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="status")
    def status(self, request):
        return Response({"message": "billing status exists"})

    @action(detail=False, methods=["post"], url_path="subscribe")
    def subscribe(self, request):
        return Response({"message": "subscribe exists"})

    @action(detail=False, methods=["post"], url_path="unsubscribe")
    def unsubscribe(self, request):
        return Response({"message": "unsubscribe exists"})


@api_view(["POST"])
@permission_classes([AllowAny])
def stripe_webhook(request):
    return Response({"message": "webhook exists"})
