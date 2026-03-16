from rest_framework.routers import DefaultRouter
from .views import ResumeViewSet

router = DefaultRouter()
router.register(r"", ResumeViewSet, basename="resumes")

urlpatterns = router.urls
