from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ATSScan


class ATSViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post"]

    def get_queryset(self):
        return ATSScan.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="scan")
    def scan(self, request):
        return Response({"message": "ats scan exists"})

    @action(detail=False, methods=["post"], url_path="match")
    def match(self, request):
        return Response({"message": "ats match exists"})

    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request):
        return Response({"message": "ats history exists"})
