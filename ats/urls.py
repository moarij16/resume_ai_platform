from rest_framework.routers import DefaultRouter
from .views import ATSViewSet

router = DefaultRouter()
router.register(r"", ATSViewSet, basename="ats")
urlpatterns = router.urls
