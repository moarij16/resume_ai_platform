"""
Tests for the jobs app.

Covers:
  - JobDescription.create_for_user model factory
  - JobDescription.update_fields_from instance method
  - JobDescriptionCreateSerializer / JobDescriptionUpdateSerializer validation
  - POST   /api/v1/jobs/          create
  - GET    /api/v1/jobs/          list (scoped to user)
  - GET    /api/v1/jobs/<id>/     retrieve
  - PATCH  /api/v1/jobs/<id>/     partial update
  - DELETE /api/v1/jobs/<id>/     destroy
"""

import uuid
from unittest.mock import MagicMock

import pytest
from rest_framework.test import APIClient

from jobs.models import JobDescription
from jobs.serializers import JobDescriptionCreateSerializer, JobDescriptionUpdateSerializer
from users.models import Users

BASE_URL = "/api/v1/jobs/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    return Users.objects.create(
        email="jobs_user@example.com",
        first_name="Job",
        last_name="Tester",
    )


@pytest.fixture
def other_user(db):
    return Users.objects.create(
        email="other_jobs@example.com",
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def job(user):
    return JobDescription.create_for_user(
        user=user,
        job_title="Software Engineer",
        company_name="Acme Corp",
        job_description_text="Build cool things.",
    )


@pytest.fixture
def other_job(other_user):
    return JobDescription.create_for_user(
        user=other_user,
        job_title="Designer",
        company_name="Other Co",
        job_description_text="Design cool things.",
    )


def _mock_request(user):
    req = MagicMock()
    req.user = user
    return req


# ---------------------------------------------------------------------------
# Model — create_for_user
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestJobDescriptionCreateForUser:

    def test_creates_and_persists(self, user):
        job = JobDescription.create_for_user(
            user=user,
            job_title="SWE",
            company_name="Corp",
            job_description_text="Do stuff.",
        )
        assert job.pk is not None
        assert JobDescription.objects.filter(pk=job.pk).exists()

    def test_fields_are_set(self, user):
        job = JobDescription.create_for_user(
            user=user,
            job_title="SWE",
            company_name="Corp",
            job_description_text="Do stuff.",
        )
        assert job.user == user
        assert job.job_title == "SWE"
        assert job.company_name == "Corp"
        assert job.job_description_text == "Do stuff."

    def test_parsed_keywords_defaults_null(self, user):
        job = JobDescription.create_for_user(
            user=user,
            job_title="SWE",
            company_name="Corp",
            job_description_text="Do stuff.",
        )
        assert job.parsed_keywords is None


# ---------------------------------------------------------------------------
# Model — update_fields_from
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestJobDescriptionUpdateFieldsFrom:

    def test_updates_job_title(self, job):
        job.update_fields_from(job_title="Senior SWE")
        job.refresh_from_db()
        assert job.job_title == "Senior SWE"

    def test_updates_company_name(self, job):
        job.update_fields_from(company_name="New Corp")
        job.refresh_from_db()
        assert job.company_name == "New Corp"

    def test_updates_description_text(self, job):
        job.update_fields_from(job_description_text="Updated JD.")
        job.refresh_from_db()
        assert job.job_description_text == "Updated JD."

    def test_partial_update_leaves_other_fields(self, job):
        original_company = job.company_name
        job.update_fields_from(job_title="Staff SWE")
        job.refresh_from_db()
        assert job.company_name == original_company

    def test_ignores_unknown_fields(self, job):
        # Should not raise; unknown keys are silently ignored
        job.update_fields_from(job_title="SWE II", unknown_field="boom")
        job.refresh_from_db()
        assert job.job_title == "SWE II"

    def test_no_fields_does_not_save(self, job):
        original_updated_at = job.updated_at
        job.update_fields_from()
        job.refresh_from_db()
        assert job.updated_at == original_updated_at


# ---------------------------------------------------------------------------
# Serializer — JobDescriptionCreateSerializer
# ---------------------------------------------------------------------------

class TestJobDescriptionCreateSerializer:

    def test_valid_data(self, user):
        s = JobDescriptionCreateSerializer(
            data={
                "job_title": "SWE",
                "company_name": "Corp",
                "job_description_text": "Do stuff.",
            },
            context={"request": _mock_request(user)},
        )
        assert s.is_valid(), s.errors

    def test_missing_job_title(self, user):
        s = JobDescriptionCreateSerializer(
            data={"company_name": "Corp", "job_description_text": "JD"},
            context={"request": _mock_request(user)},
        )
        assert not s.is_valid()
        assert "job_title" in s.errors

    def test_missing_company_name(self, user):
        s = JobDescriptionCreateSerializer(
            data={"job_title": "SWE", "job_description_text": "JD"},
            context={"request": _mock_request(user)},
        )
        assert not s.is_valid()
        assert "company_name" in s.errors

    def test_missing_description_text(self, user):
        s = JobDescriptionCreateSerializer(
            data={"job_title": "SWE", "company_name": "Corp"},
            context={"request": _mock_request(user)},
        )
        assert not s.is_valid()
        assert "job_description_text" in s.errors

    @pytest.mark.django_db
    def test_save_creates_db_record(self, user):
        s = JobDescriptionCreateSerializer(
            data={
                "job_title": "SWE",
                "company_name": "Corp",
                "job_description_text": "Do stuff.",
            },
            context={"request": _mock_request(user)},
        )
        assert s.is_valid()
        job = s.save()
        assert JobDescription.objects.filter(pk=job.pk).exists()
        assert job.user == user


# ---------------------------------------------------------------------------
# Serializer — JobDescriptionUpdateSerializer
# ---------------------------------------------------------------------------

class TestJobDescriptionUpdateSerializer:

    def test_valid_partial_data(self, user):
        s = JobDescriptionUpdateSerializer(
            data={"job_title": "Staff SWE"},
            partial=True,
        )
        assert s.is_valid(), s.errors

    def test_empty_data_is_invalid(self, user):
        s = JobDescriptionUpdateSerializer(data={}, partial=True)
        assert not s.is_valid()

    @pytest.mark.django_db
    def test_save_updates_instance(self, job):
        s = JobDescriptionUpdateSerializer(
            job,
            data={"job_title": "Principal SWE"},
            partial=True,
        )
        assert s.is_valid()
        updated = s.save()
        updated.refresh_from_db()
        assert updated.job_title == "Principal SWE"


# ---------------------------------------------------------------------------
# Endpoint — POST /api/v1/jobs/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestJobDescriptionCreate:

    def test_requires_auth(self):
        response = APIClient().post(BASE_URL, {}, format="json")
        assert response.status_code == 401

    def test_returns_201(self, auth_client):
        response = auth_client.post(
            BASE_URL,
            {"job_title": "SWE", "company_name": "Corp", "job_description_text": "JD"},
            format="json",
        )
        assert response.status_code == 201

    def test_response_shape(self, auth_client):
        response = auth_client.post(
            BASE_URL,
            {"job_title": "SWE", "company_name": "Corp", "job_description_text": "JD"},
            format="json",
        )
        data = response.json()
        for key in ("id", "job_title", "company_name", "job_description_text", "created_at", "updated_at"):
            assert key in data, f"missing key: {key}"

    def test_creates_db_record(self, auth_client, user):
        auth_client.post(
            BASE_URL,
            {"job_title": "SWE", "company_name": "Corp", "job_description_text": "JD"},
            format="json",
        )
        assert JobDescription.objects.filter(user=user, job_title="SWE").exists()

    def test_missing_required_field_returns_400(self, auth_client):
        response = auth_client.post(
            BASE_URL,
            {"job_title": "SWE", "company_name": "Corp"},  # missing job_description_text
            format="json",
        )
        assert response.status_code == 400

    def test_scoped_to_authenticated_user(self, auth_client, user):
        auth_client.post(
            BASE_URL,
            {"job_title": "SWE", "company_name": "Corp", "job_description_text": "JD"},
            format="json",
        )
        assert JobDescription.objects.get(user=user, job_title="SWE").user == user


# ---------------------------------------------------------------------------
# Endpoint — GET /api/v1/jobs/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestJobDescriptionList:

    def test_requires_auth(self):
        response = APIClient().get(BASE_URL)
        assert response.status_code == 401

    def test_returns_only_own_jobs(self, auth_client, job, other_job):
        response = auth_client.get(BASE_URL)
        assert response.status_code == 200
        titles = [j["job_title"] for j in response.json()]
        assert "Software Engineer" in titles
        assert "Designer" not in titles

    def test_empty_list_for_new_user(self, auth_client):
        response = auth_client.get(BASE_URL)
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_multiple_jobs(self, auth_client, user):
        JobDescription.create_for_user(user=user, job_title="A", company_name="C", job_description_text="JD")
        JobDescription.create_for_user(user=user, job_title="B", company_name="C", job_description_text="JD")
        response = auth_client.get(BASE_URL)
        assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# Endpoint — GET /api/v1/jobs/<id>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestJobDescriptionRetrieve:

    def test_requires_auth(self, job):
        response = APIClient().get(f"{BASE_URL}{job.pk}/")
        assert response.status_code == 401

    def test_returns_own_job(self, auth_client, job):
        response = auth_client.get(f"{BASE_URL}{job.pk}/")
        assert response.status_code == 200
        assert response.json()["id"] == str(job.pk)

    def test_cannot_access_other_users_job(self, auth_client, other_job):
        response = auth_client.get(f"{BASE_URL}{other_job.pk}/")
        assert response.status_code == 404

    def test_nonexistent_returns_404(self, auth_client):
        response = auth_client.get(f"{BASE_URL}{uuid.uuid4()}/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint — PATCH /api/v1/jobs/<id>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestJobDescriptionPartialUpdate:

    def test_requires_auth(self, job):
        response = APIClient().patch(f"{BASE_URL}{job.pk}/", {}, format="json")
        assert response.status_code == 401

    def test_updates_job_title(self, auth_client, job):
        response = auth_client.patch(
            f"{BASE_URL}{job.pk}/",
            {"job_title": "Senior SWE"},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["job_title"] == "Senior SWE"

    def test_updates_company_name(self, auth_client, job):
        response = auth_client.patch(
            f"{BASE_URL}{job.pk}/",
            {"company_name": "New Corp"},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["company_name"] == "New Corp"

    def test_persists_to_db(self, auth_client, job):
        auth_client.patch(f"{BASE_URL}{job.pk}/", {"job_title": "Staff SWE"}, format="json")
        job.refresh_from_db()
        assert job.job_title == "Staff SWE"

    def test_empty_body_returns_400(self, auth_client, job):
        response = auth_client.patch(f"{BASE_URL}{job.pk}/", {}, format="json")
        assert response.status_code == 400

    def test_cannot_update_other_users_job(self, auth_client, other_job):
        response = auth_client.patch(
            f"{BASE_URL}{other_job.pk}/",
            {"job_title": "Hacked"},
            format="json",
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint — DELETE /api/v1/jobs/<id>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestJobDescriptionDestroy:

    def test_requires_auth(self, job):
        response = APIClient().delete(f"{BASE_URL}{job.pk}/")
        assert response.status_code == 401

    def test_returns_204(self, auth_client, job):
        response = auth_client.delete(f"{BASE_URL}{job.pk}/")
        assert response.status_code == 204

    def test_record_is_deleted(self, auth_client, job):
        pk = job.pk
        auth_client.delete(f"{BASE_URL}{pk}/")
        assert not JobDescription.objects.filter(pk=pk).exists()

    def test_cannot_delete_other_users_job(self, auth_client, other_job):
        response = auth_client.delete(f"{BASE_URL}{other_job.pk}/")
        assert response.status_code == 404
        assert JobDescription.objects.filter(pk=other_job.pk).exists()
