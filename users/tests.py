"""
Tests for the users app.

Covers:
  - Users.get_or_create_from_supabase — create new, retrieve existing, update stale fields
  - Users.record_login — updates last_login timestamp
  - Users.deactivate — sets is_active=False
"""

import uuid

import pytest
from django.utils import timezone

from users.models import Users


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def supabase_uid():
    return str(uuid.uuid4())


@pytest.fixture
def existing_user(db, supabase_uid):
    return Users.objects.create(
        supabase_uid=supabase_uid,
        email="existing@example.com",
        first_name="Jane",
        last_name="Doe",
    )


# ---------------------------------------------------------------------------
# get_or_create_from_supabase
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGetOrCreateFromSupabase:

    def test_creates_new_user(self, supabase_uid):
        user, created = Users.get_or_create_from_supabase(
            supabase_uid=supabase_uid,
            email="new@example.com",
            given_name="John",
            family_name="Smith",
        )
        assert created is True
        assert user.supabase_uid == supabase_uid
        assert user.email == "new@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Smith"

    def test_returns_existing_user(self, existing_user, supabase_uid):
        user, created = Users.get_or_create_from_supabase(supabase_uid=supabase_uid)
        assert created is False
        assert user.pk == existing_user.pk

    def test_updates_stale_email(self, existing_user, supabase_uid):
        user, _ = Users.get_or_create_from_supabase(
            supabase_uid=supabase_uid,
            email="updated@example.com",
        )
        user.refresh_from_db()
        assert user.email == "updated@example.com"

    def test_updates_stale_name(self, existing_user, supabase_uid):
        user, _ = Users.get_or_create_from_supabase(
            supabase_uid=supabase_uid,
            given_name="Janet",
            family_name="Smith",
        )
        user.refresh_from_db()
        assert user.first_name == "Janet"
        assert user.last_name == "Smith"

    def test_does_not_overwrite_with_empty_values(self, existing_user, supabase_uid):
        """Passing empty strings must not blank out existing data."""
        Users.get_or_create_from_supabase(
            supabase_uid=supabase_uid,
            email="",
            given_name="",
            family_name="",
        )
        existing_user.refresh_from_db()
        assert existing_user.email == "existing@example.com"
        assert existing_user.first_name == "Jane"

    def test_records_login_on_create(self, supabase_uid):
        before = timezone.now()
        user, _ = Users.get_or_create_from_supabase(
            supabase_uid=supabase_uid,
            email="login@example.com",
        )
        assert user.last_login is not None
        assert user.last_login >= before

    def test_records_login_on_retrieve(self, existing_user, supabase_uid):
        before = timezone.now()
        user, _ = Users.get_or_create_from_supabase(supabase_uid=supabase_uid)
        assert user.last_login >= before


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

    def test_is_authenticated_returns_false_after_deactivate(self, existing_user):
        existing_user.deactivate()
        assert existing_user.is_authenticated is False

    def test_is_anonymous_always_false(self, existing_user):
        assert existing_user.is_anonymous is False
        existing_user.deactivate()
        assert existing_user.is_anonymous is False
