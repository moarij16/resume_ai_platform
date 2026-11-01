from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import AuthViewSet, LoginView, UserViewSet

router = DefaultRouter()
router.register(r"auth", AuthViewSet, basename="auth")
router.register(r"", UserViewSet, basename="users")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
] + router.urls
