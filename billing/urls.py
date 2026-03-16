from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import BillingViewSet, stripe_webhook

router = DefaultRouter()
router.register(r"", BillingViewSet, basename="billing")

urlpatterns = router.urls + [
    path("webhook/", stripe_webhook),
]
