"""
Tests for the generated_documents app.

Covers:
  - GeneratedDocument.create_for_user model factory
  - generate_cover_letter / generate_linkedin_bio / generate_resume / generate_resume_refactor
  - POST /api/v1/documents/cover-letter/
  - POST /api/v1/documents/linkedin/
  - POST /api/v1/documents/generate/
  - POST /api/v1/documents/refactor/
  - GET  /api/v1/documents/                  list (scoped)
  - GET  /api/v1/documents/<id>/download/    pdf / docx / txt
  - DELETE /api/v1/documents/<id>/           soft delete
  - renderer — render_pdf / render_docx return bytes
"""

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIClient

from generated_documents.models import DocumentType, GeneratedDocument
from generated_documents.services.renderer import render_docx, render_pdf
from generated_documents.services.templates.base import ResumeTemplate
from jobs.models import JobDescription
from resumes.models import Resume
from users.models import Users

BASE_URL = "/api/v1/documents/"

# Minimal structured JSON that the AI returns for resume/refactor types
RESUME_JSON = json.dumps({
    "summary": "Experienced software engineer.",
    "experience": [
        {
            "title": "Software Engineer",
            "company": "Acme Corp",
            "duration": "2020 - 2024",
            "bullets": ["Built scalable APIs", "Led team of 5"],
        }
    ],
    "education": [
        {"degree": "BSc Computer Science", "institution": "MIT", "year": "2019"}
    ],
    "skills": ["Python", "Django", "React"],
    "improvements_made": ["Quantified achievements", "Removed personal pronouns"],
})


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    return Users.objects.create(
        supabase_uid=str(uuid.uuid4()),
        email="docs_user@example.com",
        first_name="Doc",
        last_name="Tester",
    )


@pytest.fixture
def other_user(db):
    return Users.objects.create(
        supabase_uid=str(uuid.uuid4()),
        email="other_docs@example.com",
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def resume(user):
    return Resume.objects.create(
        user=user,
        name="Test Resume",
        resume_data={"raw_text": "Software engineer summary"},
    )


@pytest.fixture
def job(user):
    return JobDescription.create_for_user(
        user=user,
        job_title="Backend Engineer",
        company_name="Tech Co",
        job_description_text="Python, Django, REST APIs required.",
    )


@pytest.fixture
def resume_doc(user, resume):
    return GeneratedDocument.create_for_user(
        user=user,
        document_type=DocumentType.RESUME,
        document_content=RESUME_JSON,
        resume=resume,
    )


@pytest.fixture
def cover_letter_doc(user, resume):
    return GeneratedDocument.create_for_user(
        user=user,
        document_type=DocumentType.COVER_LETTER,
        document_content="Dear Hiring Manager, I am excited to apply...",
        resume=resume,
    )


def _mock_request(user):
    req = MagicMock()
    req.user = user
    return req


# ---------------------------------------------------------------------------
# Model — GeneratedDocument.create_for_user
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGeneratedDocumentCreateForUser:

    def test_creates_and_persists(self, user, resume):
        doc = GeneratedDocument.create_for_user(
            user=user,
            document_type=DocumentType.COVER_LETTER,
            document_content="Cover letter content",
            resume=resume,
        )
        assert doc.pk is not None
        assert GeneratedDocument.objects.filter(pk=doc.pk).exists()

    def test_fields_are_set(self, user, resume):
        doc = GeneratedDocument.create_for_user(
            user=user,
            document_type=DocumentType.RESUME,
            document_content=RESUME_JSON,
            resume=resume,
        )
        assert doc.user == user
        assert doc.resume == resume
        assert doc.document_type == DocumentType.RESUME
        assert doc.document_content == RESUME_JSON

    def test_job_and_resume_optional(self, user):
        doc = GeneratedDocument.create_for_user(
            user=user,
            document_type=DocumentType.LINKED_IN_BIO,
            document_content="Bio content",
        )
        assert doc.resume is None
        assert doc.job is None

    def test_with_job(self, user, resume, job):
        doc = GeneratedDocument.create_for_user(
            user=user,
            document_type=DocumentType.COVER_LETTER,
            document_content="Dear...",
            resume=resume,
            job=job,
        )
        assert doc.job == job


# ---------------------------------------------------------------------------
# Service — generate_cover_letter
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGenerateCoverLetter:

    def test_creates_document(self, user, resume):
        with patch("generated_documents.services.generator.call_ai") as mock_ai:
            mock_ai.return_value = "Dear Hiring Manager..."
            from generated_documents.services.generator import generate_cover_letter
            doc = generate_cover_letter(user=user, resume_id=resume.id)

        assert doc.pk is not None
        assert doc.document_type == DocumentType.COVER_LETTER
        assert doc.document_content == "Dear Hiring Manager..."
        assert doc.user == user

    def test_with_job(self, user, resume, job):
        with patch("generated_documents.services.generator.call_ai") as mock_ai:
            mock_ai.return_value = "Dear Tech Co..."
            from generated_documents.services.generator import generate_cover_letter
            doc = generate_cover_letter(user=user, resume_id=resume.id, job_id=job.id)

        assert doc.job == job

    def test_raises_if_resume_not_owned(self, user, other_user):
        other_resume = Resume.objects.create(user=other_user, name="Other", resume_data={})
        from generated_documents.services.generator import generate_cover_letter
        with pytest.raises(Exception):
            generate_cover_letter(user=user, resume_id=other_resume.id)


# ---------------------------------------------------------------------------
# Service — generate_linkedin_bio
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGenerateLinkedInBio:

    def test_creates_document(self, user, resume):
        with patch("generated_documents.services.generator.call_ai") as mock_ai:
            mock_ai.return_value = "Dynamic engineer with 5 years..."
            from generated_documents.services.generator import generate_linkedin_bio
            doc = generate_linkedin_bio(user=user, resume_id=resume.id)

        assert doc.document_type == DocumentType.LINKED_IN_BIO
        assert doc.document_content == "Dynamic engineer with 5 years..."


# ---------------------------------------------------------------------------
# Service — generate_resume / generate_resume_refactor
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGenerateResume:

    def test_generates_resume(self, user, resume):
        with patch("generated_documents.services.generator.call_ai") as mock_ai:
            mock_ai.return_value = RESUME_JSON
            from generated_documents.services.generator import generate_resume
            doc = generate_resume(user=user, resume_id=resume.id)

        assert doc.document_type == DocumentType.RESUME
        assert doc.document_content == RESUME_JSON

    def test_generates_refactor(self, user, resume):
        with patch("generated_documents.services.generator.call_ai") as mock_ai:
            mock_ai.return_value = RESUME_JSON
            from generated_documents.services.generator import generate_resume_refactor
            doc = generate_resume_refactor(user=user, resume_id=resume.id)

        assert doc.document_type == DocumentType.RESUME_REFACTOR


# ---------------------------------------------------------------------------
# Endpoint — POST /api/v1/documents/cover-letter/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCoverLetterEndpoint:

    def test_requires_auth(self, resume):
        response = APIClient().post(f"{BASE_URL}cover-letter/", {"resume_id": str(resume.id)}, format="json")
        assert response.status_code == 401

    def test_returns_201(self, auth_client, resume):
        with patch("generated_documents.services.generator.call_ai") as mock_ai:
            mock_ai.return_value = "Dear Hiring Manager..."
            response = auth_client.post(
                f"{BASE_URL}cover-letter/", {"resume_id": str(resume.id)}, format="json"
            )
        assert response.status_code == 201

    def test_response_shape(self, auth_client, resume):
        with patch("generated_documents.services.generator.call_ai") as mock_ai:
            mock_ai.return_value = "Dear Hiring Manager..."
            response = auth_client.post(
                f"{BASE_URL}cover-letter/", {"resume_id": str(resume.id)}, format="json"
            )
        data = response.json()
        for key in ("id", "document_type", "document_content", "created_at"):
            assert key in data, f"missing key: {key}"

    def test_missing_resume_id_returns_400(self, auth_client):
        response = auth_client.post(f"{BASE_URL}cover-letter/", {}, format="json")
        assert response.status_code == 400

    def test_invalid_resume_id_returns_404_or_400(self, auth_client):
        with patch("generated_documents.services.generator.call_ai"):
            response = auth_client.post(
                f"{BASE_URL}cover-letter/",
                {"resume_id": str(uuid.uuid4())},
                format="json",
            )
        assert response.status_code in (400, 404)


# ---------------------------------------------------------------------------
# Endpoint — POST /api/v1/documents/generate/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestResumeGenerateEndpoint:

    def test_returns_201(self, auth_client, resume):
        with patch("generated_documents.services.generator.call_ai") as mock_ai:
            mock_ai.return_value = RESUME_JSON
            response = auth_client.post(
                f"{BASE_URL}generate/", {"resume_id": str(resume.id)}, format="json"
            )
        assert response.status_code == 201

    def test_document_type_is_resume(self, auth_client, resume):
        with patch("generated_documents.services.generator.call_ai") as mock_ai:
            mock_ai.return_value = RESUME_JSON
            response = auth_client.post(
                f"{BASE_URL}generate/", {"resume_id": str(resume.id)}, format="json"
            )
        assert response.json()["document_type"] == DocumentType.RESUME


# ---------------------------------------------------------------------------
# Endpoint — POST /api/v1/documents/refactor/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestResumeRefactorEndpoint:

    def test_returns_201(self, auth_client, resume):
        with patch("generated_documents.services.generator.call_ai") as mock_ai:
            mock_ai.return_value = RESUME_JSON
            response = auth_client.post(
                f"{BASE_URL}refactor/", {"resume_id": str(resume.id)}, format="json"
            )
        assert response.status_code == 201

    def test_document_type_is_resume_refactor(self, auth_client, resume):
        with patch("generated_documents.services.generator.call_ai") as mock_ai:
            mock_ai.return_value = RESUME_JSON
            response = auth_client.post(
                f"{BASE_URL}refactor/", {"resume_id": str(resume.id)}, format="json"
            )
        assert response.json()["document_type"] == DocumentType.RESUME_REFACTOR


# ---------------------------------------------------------------------------
# Endpoint — GET /api/v1/documents/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGeneratedDocumentList:

    def test_requires_auth(self):
        response = APIClient().get(BASE_URL)
        assert response.status_code == 401

    def test_returns_only_own_documents(self, auth_client, user, other_user, resume_doc):
        other_resume = Resume.objects.create(user=other_user, name="Other", resume_data={})
        GeneratedDocument.create_for_user(
            user=other_user,
            document_type=DocumentType.COVER_LETTER,
            document_content="Not mine",
            resume=other_resume,
        )
        response = auth_client.get(BASE_URL)
        assert response.status_code == 200
        ids = [d["id"] for d in response.json()]
        assert str(resume_doc.pk) in ids
        # only one doc belongs to user
        assert len(ids) == 1

    def test_empty_for_new_user(self, auth_client):
        response = auth_client.get(BASE_URL)
        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# Endpoint — DELETE /api/v1/documents/<id>/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGeneratedDocumentDelete:

    def test_returns_204(self, auth_client, resume_doc):
        response = auth_client.delete(f"{BASE_URL}{resume_doc.pk}/")
        assert response.status_code == 204

    def test_record_soft_deleted(self, auth_client, resume_doc):
        pk = resume_doc.pk
        auth_client.delete(f"{BASE_URL}{pk}/")
        # SoftDeleteManager hides it from .objects — must use all_objects or direct field check
        from core.base import AllObjectsManager
        resume_doc.refresh_from_db()
        assert resume_doc.is_deleted is True

    def test_cannot_delete_other_users_document(self, auth_client, other_user):
        other_resume = Resume.objects.create(user=other_user, name="Other", resume_data={})
        other_doc = GeneratedDocument.create_for_user(
            user=other_user,
            document_type=DocumentType.COVER_LETTER,
            document_content="Not yours",
            resume=other_resume,
        )
        response = auth_client.delete(f"{BASE_URL}{other_doc.pk}/")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Endpoint — GET /api/v1/documents/<id>/download/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDownloadEndpoint:

    def test_requires_auth(self, resume_doc):
        response = APIClient().get(f"{BASE_URL}{resume_doc.pk}/download/")
        assert response.status_code == 401

    def test_download_pdf(self, auth_client, resume_doc):
        with patch("generated_documents.views.render_pdf") as mock_pdf:
            mock_pdf.return_value = b"%PDF-fake"
            response = auth_client.get(f"{BASE_URL}{resume_doc.pk}/download/?file_format=pdf")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert ".pdf" in response["Content-Disposition"]

    def test_download_docx(self, auth_client, resume_doc):
        with patch("generated_documents.views.render_docx") as mock_docx:
            mock_docx.return_value = b"PKfake-docx"
            response = auth_client.get(f"{BASE_URL}{resume_doc.pk}/download/?file_format=docx")
        assert response.status_code == 200
        assert "wordprocessingml" in response["Content-Type"]
        assert ".docx" in response["Content-Disposition"]

    def test_download_txt(self, auth_client, resume_doc):
        response = auth_client.get(f"{BASE_URL}{resume_doc.pk}/download/?file_format=txt")
        assert response.status_code == 200
        assert response["Content-Type"] == "text/plain"

    def test_pdf_disallowed_for_cover_letter(self, auth_client, cover_letter_doc):
        response = auth_client.get(f"{BASE_URL}{cover_letter_doc.pk}/download/?file_format=pdf")
        assert response.status_code == 400

    def test_docx_disallowed_for_linkedin_bio(self, auth_client, user, resume):
        bio_doc = GeneratedDocument.create_for_user(
            user=user,
            document_type=DocumentType.LINKED_IN_BIO,
            document_content="Bio text",
            resume=resume,
        )
        response = auth_client.get(f"{BASE_URL}{bio_doc.pk}/download/?file_format=docx")
        assert response.status_code == 400

    def test_unsupported_format_returns_400(self, auth_client, resume_doc):
        response = auth_client.get(f"{BASE_URL}{resume_doc.pk}/download/?file_format=xlsx")
        assert response.status_code == 400

    def test_default_format_is_pdf(self, auth_client, resume_doc):
        with patch("generated_documents.views.render_pdf") as mock_pdf:
            mock_pdf.return_value = b"%PDF-fake"
            response = auth_client.get(f"{BASE_URL}{resume_doc.pk}/download/")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"

    def test_cannot_download_other_users_document(self, auth_client, other_user):
        other_resume = Resume.objects.create(user=other_user, name="Other", resume_data={})
        other_doc = GeneratedDocument.create_for_user(
            user=other_user,
            document_type=DocumentType.RESUME,
            document_content=RESUME_JSON,
            resume=other_resume,
        )
        response = auth_client.get(f"{BASE_URL}{other_doc.pk}/download/?file_format=txt")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Renderer — unit tests (no HTTP, no DB)
# ---------------------------------------------------------------------------

class TestRendererPDF:
    """render_pdf must return non-empty bytes starting with %PDF."""

    def _make_doc(self):
        user = MagicMock()
        user.first_name = "Jane"
        user.last_name = "Doe"
        user.email = "jane@example.com"
        doc = MagicMock()
        doc.document_content = RESUME_JSON
        doc.user = user
        return doc

    def test_returns_bytes(self):
        result = render_pdf(self._make_doc())
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_is_pdf(self):
        result = render_pdf(self._make_doc())
        assert result[:4] == b"%PDF"

    def test_missing_sections_do_not_crash(self):
        user = MagicMock()
        user.first_name = "Jane"
        user.last_name = "Doe"
        user.email = "jane@example.com"
        doc = MagicMock()
        doc.document_content = json.dumps({"summary": "Only a summary."})
        doc.user = user
        result = render_pdf(doc)
        assert isinstance(result, bytes)

    def test_empty_content_does_not_crash(self):
        user = MagicMock()
        user.first_name = ""
        user.last_name = ""
        user.email = "x@example.com"
        doc = MagicMock()
        doc.document_content = "{}"
        doc.user = user
        result = render_pdf(doc)
        assert isinstance(result, bytes)


class TestRendererDOCX:
    """render_docx must return non-empty bytes with a valid DOCX PK signature."""

    def _make_doc(self):
        user = MagicMock()
        user.first_name = "Jane"
        user.last_name = "Doe"
        user.email = "jane@example.com"
        doc = MagicMock()
        doc.document_content = RESUME_JSON
        doc.user = user
        return doc

    def test_returns_bytes(self):
        result = render_docx(self._make_doc())
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_is_zip_docx(self):
        result = render_docx(self._make_doc())
        # DOCX files are ZIP archives; all start with PK\x03\x04
        assert result[:2] == b"PK"

    def test_missing_sections_do_not_crash(self):
        user = MagicMock()
        user.first_name = "Jane"
        user.last_name = "Doe"
        user.email = "jane@example.com"
        doc = MagicMock()
        doc.document_content = json.dumps({"skills": ["Python"]})
        doc.user = user
        result = render_docx(doc)
        assert isinstance(result, bytes)


class TestResumeTemplateBase:
    """Shared utilities on the base class."""

    def test_parse_content_valid_json(self):
        result = ResumeTemplate.parse_content('{"summary": "hello"}')
        assert result == {"summary": "hello"}

    def test_parse_content_invalid_json_returns_empty(self):
        result = ResumeTemplate.parse_content("not json {{{")
        assert result == {}

    def test_parse_content_none_returns_empty(self):
        result = ResumeTemplate.parse_content(None)
        assert result == {}

    def test_full_name_with_both_names(self):
        user = MagicMock()
        user.first_name = "Jane"
        user.last_name = "Doe"
        user.email = "jane@example.com"
        assert ResumeTemplate.full_name(user) == "Jane Doe"

    def test_full_name_falls_back_to_email(self):
        user = MagicMock()
        user.first_name = ""
        user.last_name = ""
        user.email = "jane@example.com"
        assert ResumeTemplate.full_name(user) == "jane@example.com"
