from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Object-level check: the object must belong to the requesting user.

    Owned ViewSets already scope their queryset to the user (so other users'
    records 404 rather than 403, which avoids leaking that they exist). This is
    the second line of defence for any code path that fetches objects another way.
    """

    message = "You do not have access to this resource."

    def has_object_permission(self, request, view, obj):
        is_owned_by = getattr(obj, "is_owned_by", None)
        if callable(is_owned_by):
            return is_owned_by(request.user)
        return getattr(obj, "user_id", None) == getattr(request.user, "pk", None)
