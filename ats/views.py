from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ATSScan
from .serializers import ATSScanInputSerializer, ATSScanSerializer
from .services.ats_service import run_scan


class ATSViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ATSScanSerializer

    def get_queryset(self):
        return ATSScan.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="scan")
    def scan(self, request):
        serializer = ATSScanInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resume_id = serializer.validated_data["resume_id"]
        job_id = serializer.validated_data.get("job_id")

        try:
            scan = run_scan(user=request.user, resume_id=resume_id, job_id=job_id)
        except Exception as e:
            return Response(
                {"error": True, "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(ATSScanSerializer(scan).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request):
        scans = self.get_queryset().order_by("-created_at")
        return Response(ATSScanSerializer(scans, many=True).data)
