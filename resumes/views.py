from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Resume


class ResumeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        return Response({"message": "upload resume exists"})

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        return Response({"message": "resume generate exists"})

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        return Response({"message": f"resume {pk} download exists"})
