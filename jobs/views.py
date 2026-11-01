from rest_framework import status, viewsets
from rest_framework.response import Response

from core.mixins import OwnedResourceMixin

from .models import JobDescription
from .serializers import (
    JobDescriptionCreateSerializer,
    JobDescriptionSerializer,
    JobDescriptionUpdateSerializer,
)


class JobDescriptionViewSet(OwnedResourceMixin, viewsets.ModelViewSet):
    owned_model = JobDescription
    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = JobDescriptionSerializer

    def create(self, request, *args, **kwargs):
        serializer = JobDescriptionCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        return Response(JobDescriptionSerializer(job).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = JobDescriptionUpdateSerializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        job = serializer.save()
        return Response(JobDescriptionSerializer(job).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
