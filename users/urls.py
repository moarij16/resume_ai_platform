from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet

router = DefaultRouter()
router.register(r"", UserProfileViewSet, basename="users")

urlpatterns = router.urls
