from rest_framework.routers import DefaultRouter
from .views import GeneratedDocumentViewSet

router = DefaultRouter()
router.register(r"", GeneratedDocumentViewSet, basename="generated-documents")
urlpatterns = router.urls
