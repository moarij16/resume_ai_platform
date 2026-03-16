from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import GeneratedDocument


# Create your views here.
class GeneratedDocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "delete"]

    def get_queryset(self):
        return GeneratedDocument.objects.filter(user=self.request.user)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        return Response({"message": f"generated document {pk} download exists"})
