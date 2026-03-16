from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class ResumeViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        return Response({"message": "list resumes exists"})

    def create(self, request):
        return Response({"message": "create resume exists"})

    def retrieve(self, request, pk=None):
        return Response({"message": f"resume {pk} exists"})

    def partial_update(self, request, pk=None):
        return Response({"message": f"resume {pk} update exists"})

    def destroy(self, request, pk=None):
        return Response({"message": f"resume {pk} delete exists"})

    # Custom actions for non-standard endpoints
    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        return Response({"message": "upload exists"})

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        return Response({"message": "generate exists"})

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        return Response({"message": f"resume {pk} download exists"})

    @action(detail=False, methods=["get"], url_path="templates")
    def templates(self, request):
        return Response({"message": "templates exists"})
