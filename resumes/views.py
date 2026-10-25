from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ats.serializers import ATSScanSerializer
from ats.services.ats_service import run_scan
from core.mixins import OwnedResourceMixin

from .models import Resume
from .serializers import (
    ResumeSerializer,
    ResumeUpdateSerializer,
    ResumeUploadSerializer,
)


class ResumeViewSet(OwnedResourceMixin, viewsets.ModelViewSet):
    owned_model = Resume
    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = ResumeSerializer

    def partial_update(self, request, *args, **kwargs):
        resume = self.get_object()
        serializer = ResumeUpdateSerializer(
            resume, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        updated_resume = serializer.save()
        return Response(ResumeSerializer(updated_resume).data)

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        serializer = ResumeUploadSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        resume = serializer.save()

        try:
            scan = run_scan(user=request.user, resume_id=resume.id)
        except Exception as e:
            return Response(
                {"error": True, "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "resume": ResumeSerializer(resume).data,
                "ats_scan": ATSScanSerializer(scan).data,
            },
            status=status.HTTP_201_CREATED,
        )
