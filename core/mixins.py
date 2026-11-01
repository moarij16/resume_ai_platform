from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsOwner


class SoftDeleteMixin(GenericAPIView):
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OwnedResourceMixin:
    """
    Access policy for ViewSets over a `UserOwnedModel`: a user can only list,
    retrieve, change or delete their own, non-deleted records.

    Set `owned_model` on the ViewSet. Records belonging to other users, or
    soft-deleted ones, are simply not in the queryset, so they return 404.
    """

    owned_model = None
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        assert self.owned_model is not None, f"{type(self).__name__} must set `owned_model`."
        return self.owned_model.owned_by(self.request.user)
