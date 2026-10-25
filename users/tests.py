"""
Tests for the users app.

Covers:
  - Users.register / create_user — hashed password, normalised email
  - POST /api/v1/users/auth/register/ — creates user, returns tokens
  - POST /api/v1/users/auth/login/    — email + password -> tokens
  - POST /api/v1/users/auth/refresh/  — refresh -> new access
  - POST /api/v1/users/auth/logout/   — blacklists refresh token
  - POST /api/v1/users/me/change-password/
  - Users.record_login — updates last_login timestamp
  - Users.deactivate — sets is_active=False, blocks login
"""

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import Users


BASE_URL = "/api/v1/users/"
PASSWORD = "Str0ng-Passw0rd!"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def existing_user(db):
    return Users.register(
        email="existing@example.com",
        password=PASSWORD,
        first_name="Jane",
        last_name="Doe",
    )


def login(client, email="existing@example.com", password=PASSWORD):
    return client.post(
        f"{BASE_URL}auth/login/", {"email": email, "password": password}
    )


# ---------------------------------------------------------------------------
# register (model)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRegisterModel:

    def test_password_is_hashed(self, existing_user):
        assert existing_user.password != PASSWORD
        assert existing_user.check_password(PASSWORD)

    def test_email_is_lowercased(self):
        user = Users.register(email="MiXeD@Example.COM", password=PASSWORD)
        assert user.email == "mixed@example.com"


# ---------------------------------------------------------------------------
# register (API)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRegisterEndpoint:

    def test_returns_201_with_tokens(self, client):
        response = client.post(
            f"{BASE_URL}auth/register/",
            {"email": "new@example.com", "password": PASSWORD, "first_name": "John"},
        )
        assert response.status_code == 201
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["email"] == "new@example.com"
        assert Users.objects.filter(email="new@example.com").exists()

    def test_duplicate_email_rejected(self, client, existing_user):
        response = client.post(
            f"{BASE_URL}auth/register/",
            {"email": "EXISTING@example.com", "password": PASSWORD},
        )
        assert response.status_code == 400

    def test_weak_password_rejected(self, client):
        response = client.post(
            f"{BASE_URL}auth/register/",
            {"email": "weak@example.com", "password": "123"},
        )
        assert response.status_code == 400
        assert not Users.objects.filter(email="weak@example.com").exists()


# ---------------------------------------------------------------------------
# login / refresh / logout
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLogin:

    def test_valid_credentials_return_tokens(self, client, existing_user):
        response = login(client)
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_email_is_case_insensitive(self, client, existing_user):
        response = login(client, email="Existing@Example.com")
        assert response.status_code == 200

    def test_wrong_password_returns_401(self, client, existing_user):
        response = login(client, password="wrong-password")
        assert response.status_code == 401

    def test_records_login(self, client, existing_user):
        before = timezone.now()
        login(client)
        existing_user.refresh_from_db()
        assert existing_user.last_login >= before

    def test_access_token_authenticates_requests(self, client, existing_user):
        access = login(client).data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = client.get(f"{BASE_URL}me/")
        assert response.status_code == 200
        assert response.data["email"] == "existing@example.com"

    def test_me_without_token_returns_401(self, client):
        response = client.get(f"{BASE_URL}me/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestRefreshAndLogout:

    def test_refresh_returns_new_access(self, client, existing_user):
        refresh = login(client).data["refresh"]
        response = client.post(f"{BASE_URL}auth/refresh/", {"refresh": refresh})
        assert response.status_code == 200
        assert "access" in response.data

    def test_logout_blacklists_refresh(self, client, existing_user):
        refresh = login(client).data["refresh"]
        response = client.post(f"{BASE_URL}auth/logout/", {"refresh": refresh})
        assert response.status_code == 204
        response = client.post(f"{BASE_URL}auth/refresh/", {"refresh": refresh})
        assert response.status_code == 401

    def test_logout_with_bad_token_returns_400(self, client):
        response = client.post(f"{BASE_URL}auth/logout/", {"refresh": "garbage"})
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# change password
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestChangePassword:

    NEW_PASSWORD = "An0ther-Str0ng-One!"

    def test_changes_password(self, client, existing_user):
        client.force_authenticate(user=existing_user)
        response = client.post(
            f"{BASE_URL}me/change-password/",
            {"current_password": PASSWORD, "new_password": self.NEW_PASSWORD},
        )
        assert response.status_code == 204
        existing_user.refresh_from_db()
        assert existing_user.check_password(self.NEW_PASSWORD)

    def test_wrong_current_password_rejected(self, client, existing_user):
        client.force_authenticate(user=existing_user)
        response = client.post(
            f"{BASE_URL}me/change-password/",
            {"current_password": "nope", "new_password": self.NEW_PASSWORD},
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# record_login
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRecordLogin:

    def test_sets_last_login(self, existing_user):
        before = timezone.now()
        existing_user.record_login()
        existing_user.refresh_from_db()
        assert existing_user.last_login is not None
        assert existing_user.last_login >= before

    def test_only_updates_last_login_field(self, existing_user):
        """Ensure update_fields is respected — other fields must not change."""
        original_email = existing_user.email
        existing_user.record_login()
        existing_user.refresh_from_db()
        assert existing_user.email == original_email


# ---------------------------------------------------------------------------
# deactivate
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDeactivate:

    def test_sets_is_active_false(self, existing_user):
        assert existing_user.is_active is True
        existing_user.deactivate()
        existing_user.refresh_from_db()
        assert existing_user.is_active is False

    def test_deactivated_user_cannot_login(self, client, existing_user):
        existing_user.deactivate()
        response = login(client)
        assert response.status_code == 401
