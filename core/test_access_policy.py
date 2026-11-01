"""
Tests for the user-owned resource access policy and AI error handling.

Covers:
  - Owned ViewSets: other users' and soft-deleted records are invisible (404 / excluded)
  - OwnedResourceIdField: foreign resume/job IDs are rejected on generate and scan inputs
  - IsOwner object permission
  - AI failures surface as friendly 503s without provider error text
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from ats.models import ATSScan, ScanMode
from core.permissions import IsOwner
from generated_documents.models import DocumentType, GeneratedDocument
from jobs.models import JobDescription
from resumes.models import Resume
from users.models import Users

RESUME_TEXT = "Jane Tester. Frontend engineer with React and TypeScript experience. " * 5


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    return Users.objects.create(email="owner@example.com")


@pytest.fixture
def other_user(db):
    return Users.objects.create(email="intruder@example.com")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _records_for(owner):
    resume = Resume.objects.create(user=owner, name="CV", resume_data={"raw_text": RESUME_TEXT})
    job = JobDescription.objects.create(
        user=owner, job_title="Engineer", company_name="Acme", job_description_text="React " * 20
    )
    scan = ATSScan.objects.create(
        user=owner, resume=resume, scan_mode=ScanMode.RESUME_ONLY, ats_score=50.0
    )
    document = GeneratedDocument.objects.create(
        user=owner, resume=resume, document_type=DocumentType.COVER_LETTER, document_content="Dear team"
    )
    return {"resumes": resume, "jobs": job, "ats": scan, "documents": document}


@pytest.fixture
def mine(user):
    return _records_for(user)


@pytest.fixture
def theirs(other_user):
    return _records_for(other_user)


RESOURCES = ["resumes", "jobs", "ats", "documents"]


# ---------------------------------------------------------------------------
# Owned ViewSets
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOwnedViewSets:

    @pytest.mark.parametrize("resource", RESOURCES)
    def test_list_only_returns_own_records(self, auth_client, mine, theirs, resource):
        response = auth_client.get(f"/api/v1/{resource}/")
        assert response.status_code == 200
        assert [item["id"] for item in response.json()] == [str(mine[resource].pk)]

    @pytest.mark.parametrize("resource", RESOURCES)
    def test_other_users_record_is_not_found(self, auth_client, theirs, resource):
        response = auth_client.get(f"/api/v1/{resource}/{theirs[resource].pk}/")
        assert response.status_code == 404

    @pytest.mark.parametrize("resource", ["resumes", "jobs", "documents"])
    def test_cannot_delete_other_users_record(self, auth_client, theirs, resource):
        response = auth_client.delete(f"/api/v1/{resource}/{theirs[resource].pk}/")
        assert response.status_code == 404
        assert type(theirs[resource]).objects.filter(pk=theirs[resource].pk).exists()

    def test_cannot_patch_other_users_resume(self, auth_client, theirs):
        response = auth_client.patch(f"/api/v1/resumes/{theirs['resumes'].pk}/", {"name": "pwned"}, format="json")
        assert response.status_code == 404
        theirs["resumes"].refresh_from_db()
        assert theirs["resumes"].name == "CV"

    @pytest.mark.parametrize("resource", ["resumes", "jobs", "documents"])
    def test_deleted_records_disappear_from_list_and_detail(self, auth_client, mine, resource):
        record = mine[resource]
        assert auth_client.delete(f"/api/v1/{resource}/{record.pk}/").status_code == 204

        assert str(record.pk) not in [item["id"] for item in auth_client.get(f"/api/v1/{resource}/").json()]
        assert auth_client.get(f"/api/v1/{resource}/{record.pk}/").status_code == 404
        # Soft delete: the row is kept and still reachable through all_objects.
        assert type(record).all_objects.get(pk=record.pk).is_deleted

    def test_scan_history_is_scoped(self, auth_client, mine, theirs):
        ids = [item["id"] for item in auth_client.get("/api/v1/ats/history/").json()]
        assert ids == [str(mine["ats"].pk)]

    @pytest.mark.parametrize("resource", RESOURCES)
    def test_requires_authentication(self, resource):
        assert APIClient().get(f"/api/v1/{resource}/").status_code == 401


# ---------------------------------------------------------------------------
# Referenced IDs in request bodies
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestOwnedResourceIdField:

    @pytest.mark.parametrize("endpoint", ["cover-letter", "linkedin", "refactor", "generate"])
    def test_generation_rejects_other_users_resume(self, auth_client, theirs, endpoint):
        response = auth_client.post(
            f"/api/v1/documents/{endpoint}/", {"resume_id": str(theirs["resumes"].pk)}, format="json"
        )
        assert response.status_code == 400
        assert response.json()["detail"]["resume_id"] == ["Resume not found."]

    def test_generation_rejects_other_users_job(self, auth_client, mine, theirs):
        response = auth_client.post(
            "/api/v1/documents/cover-letter/",
            {"resume_id": str(mine["resumes"].pk), "job_id": str(theirs["jobs"].pk)},
            format="json",
        )
        assert response.status_code == 400
        assert response.json()["detail"]["job_id"] == ["Job description not found."]

    def test_generation_rejects_own_deleted_resume(self, auth_client, mine):
        mine["resumes"].delete()
        response = auth_client.post(
            "/api/v1/documents/linkedin/", {"resume_id": str(mine["resumes"].pk)}, format="json"
        )
        assert response.status_code == 400

    def test_scan_rejects_other_users_resume(self, auth_client, theirs):
        response = auth_client.post(
            "/api/v1/ats/scan/", {"resume_id": str(theirs["resumes"].pk)}, format="json"
        )
        assert response.status_code == 400
        assert response.json()["detail"]["resume_id"] == ["Resume not found."]

    def test_scan_accepts_null_job(self, auth_client, mine):
        response = auth_client.post(
            "/api/v1/ats/scan/", {"resume_id": str(mine["resumes"].pk), "job_id": None}, format="json"
        )
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# IsOwner
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_is_owner_permission(user, other_user, mine):
    permission = IsOwner()
    request_as = lambda u: SimpleNamespace(user=u)  # noqa: E731
    assert permission.has_object_permission(request_as(user), None, mine["resumes"])
    assert not permission.has_object_permission(request_as(other_user), None, mine["resumes"])


# ---------------------------------------------------------------------------
# AI error handling
# ---------------------------------------------------------------------------

PROVIDER_SECRET_TEXT = "Error code: 401 - You didn't provide an API key"


@pytest.mark.django_db
class TestAIErrors:

    def _generate(self, auth_client, mine):
        return auth_client.post(
            "/api/v1/documents/linkedin/", {"resume_id": str(mine["resumes"].pk)}, format="json"
        )

    @override_settings(AI_PROVIDER="openai", OPENAI_API_KEY="")
    def test_missing_api_key_is_a_friendly_503(self, auth_client, mine):
        response = self._generate(auth_client, mine)
        assert response.status_code == 503
        assert response.json()["detail"]["detail"] == (
            "AI features are not available right now. Please try again later."
        )

    @override_settings(AI_PROVIDER="not-a-provider")
    def test_unknown_provider_is_a_friendly_503(self, auth_client, mine):
        assert self._generate(auth_client, mine).status_code == 503

    @override_settings(AI_PROVIDER="gemini", GEMINI_API_KEY="test-key")
    def test_provider_error_text_is_not_returned(self, auth_client, mine):
        with patch("core.ai.gemini_provider.GeminiProvider.generate", side_effect=RuntimeError(PROVIDER_SECRET_TEXT)):
            response = self._generate(auth_client, mine)
        assert response.status_code == 503
        assert PROVIDER_SECRET_TEXT not in response.content.decode()
        assert response.json()["detail"]["detail"] == "AI generation failed. Please try again."
        assert not GeneratedDocument.objects.filter(document_type=DocumentType.LINKED_IN_BIO).exists()

    @override_settings(AI_PROVIDER="gemini", GEMINI_API_KEY="test-key")
    def test_rate_limit_gets_its_own_message(self, auth_client, mine):
        error = RuntimeError("429 RESOURCE_EXHAUSTED")
        error.code = 429
        with patch("core.ai.gemini_provider.GeminiProvider.generate", side_effect=error):
            response = self._generate(auth_client, mine)
        assert response.status_code == 503
        assert "busy" in response.json()["detail"]["detail"]
