from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """Only admin role users can access."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsPremiumUser(BasePermission):
    """Only premium plan users can access."""

    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated and request.user.is_premium
        )


class IsWithinUsageLimit(BasePermission):
    """
    Used on AI endpoints — checks free tier limits.
    The view must set `usage_feature` attribute.
    Example:
        class ResumeImproveView(ViewSet):
            usage_feature = "resume_improvements"
    """

    def has_permission(self, request, view):
        feature = getattr(view, "usage_feature", None)
        if not feature:
            return True
        return request.user.is_within_limits(feature)
