"""
Tests for the resumes app.

Covers:
  - ResumeUploadSerializer validation (file type, file size)
  - Resume.create_from_upload model factory
  - POST /api/v1/resumes/upload/ view (auth, happy path, bad input)
  - GET  /api/v1/resumes/ view (scoped to authenticated user)
"""

import io
import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from resumes.models import Resume
from resumes.serializers import ResumeUploadSerializer
from users.models import Users


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    return Users.objects.create(
        supabase_uid=str(uuid.uuid4()),
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def other_user(db):
    return Users.objects.create(
        supabase_uid=str(uuid.uuid4()),
        email="other@example.com",
    )


@pytest.fixture
def auth_client(user):
    """APIClient with the test user force-authenticated."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def pdf_file():
    return SimpleUploadedFile(
        "resume.pdf",
        b"%PDF-1.4 fake pdf content",
        content_type="application/pdf",
    )


@pytest.fixture
def docx_file():
    return SimpleUploadedFile(
        "resume.docx",
        b"PK fake docx content",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@pytest.fixture
def oversized_file():
    return SimpleUploadedFile(
        "big.pdf",
        b"x" * (6 * 1024 * 1024),  # 6 MB — over the 5 MB limit
        content_type="application/pdf",
    )


PARSED_DATA = {
    "raw_text": "John Doe Software Engineer",
    "word_count": 4,
    "metadata": {"file_type": "pdf", "page_count": 1, "has_images": False, "has_tables": False, "encoding_issues": []},
    "sections": {},
    "detected_skills": ["Python"],
    "skills_detail": {},
    "bullets": {},
    "experience": {},
}


# ---------------------------------------------------------------------------
# ResumeUploadSerializer — validation
# ---------------------------------------------------------------------------

class TestResumeUploadSerializerValidation:

    def test_accepts_pdf(self, user, pdf_file):
        s = ResumeUploadSerializer(
            data={"file": pdf_file, "name": "My Resume"},
            context={"request": _mock_request(user)},
        )
        assert s.is_valid(), s.errors

    def test_accepts_docx(self, user, docx_file):
        s = ResumeUploadSerializer(
            data={"file": docx_file, "name": "My Resume"},
            context={"request": _mock_request(user)},
        )
        assert s.is_valid(), s.errors

    def test_rejects_txt_extension(self, user):
        txt = SimpleUploadedFile("cv.txt", b"hello", content_type="text/plain")
        s = ResumeUploadSerializer(
            data={"file": txt},
            context={"request": _mock_request(user)},
        )
        assert not s.is_valid()
        assert "file" in s.errors

    def test_rejects_oversized_file(self, user, oversized_file):
        s = ResumeUploadSerializer(
            data={"file": oversized_file},
            context={"request": _mock_request(user)},
        )
        assert not s.is_valid()
        assert "file" in s.errors

    def test_name_is_optional(self, user, pdf_file):
        s = ResumeUploadSerializer(
            data={"file": pdf_file},
            context={"request": _mock_request(user)},
        )
        assert s.is_valid(), s.errors

    def test_name_defaults_to_filename_stem(self, user, pdf_file):
        """When name is omitted, serializer.save() falls back to the file stem."""
        with patch("resumes.services.resume_service.upload_and_parse") as mock_parse:
            mock_parse.return_value = {"file_url": "/media/r.pdf", "parsed_data": PARSED_DATA}
            s = ResumeUploadSerializer(
                data={"file": pdf_file},
                context={"request": _mock_request(user)},
            )
            assert s.is_valid()
            resume = s.save()
        assert resume.name == "resume"  # stem of "resume.pdf"


# ---------------------------------------------------------------------------
# Resume model — create_from_upload
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestResumeCreateFromUpload:

    def test_creates_resume_record(self, user, pdf_file):
        with patch("resumes.services.resume_service.upload_and_parse") as mock_parse:
            mock_parse.return_value = {"file_url": "/media/r.pdf", "parsed_data": PARSED_DATA}
            resume = Resume.create_from_upload(user, pdf_file, "Test Resume")

        assert resume.pk is not None
        assert resume.user == user
        assert resume.name == "Test Resume"
        assert resume.resume_version == 1
        assert resume.resume_data == PARSED_DATA
        assert resume.original_file_url == "/media/r.pdf"

    def test_resume_is_persisted(self, user, pdf_file):
        with patch("resumes.services.resume_service.upload_and_parse") as mock_parse:
            mock_parse.return_value = {"file_url": "/media/r.pdf", "parsed_data": PARSED_DATA}
            resume = Resume.create_from_upload(user, pdf_file, "Test Resume")

        assert Resume.objects.filter(pk=resume.pk).exists()

    def test_calls_upload_and_parse_with_correct_args(self, user, pdf_file):
        with patch("resumes.services.resume_service.upload_and_parse") as mock_parse:
            mock_parse.return_value = {"file_url": "/media/r.pdf", "parsed_data": PARSED_DATA}
            Resume.create_from_upload(user, pdf_file, "CV")

        mock_parse.assert_called_once_with(user, pdf_file)


# ---------------------------------------------------------------------------
# Upload endpoint — POST /api/v1/resumes/upload/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestResumeUploadView:

    def test_requires_auth(self, pdf_file):
        client = APIClient()
        response = client.post("/api/v1/resumes/upload/", {"file": pdf_file}, format="multipart")
        assert response.status_code == 401

    def test_upload_returns_201(self, auth_client, pdf_file):
        with patch("resumes.services.resume_service.upload_and_parse") as mock_parse:
            mock_parse.return_value = {"file_url": "/media/r.pdf", "parsed_data": PARSED_DATA}
            response = auth_client.post(
                "/api/v1/resumes/upload/",
                {"file": pdf_file, "name": "My CV"},
                format="multipart",
            )
        assert response.status_code == 201

    def test_upload_response_shape(self, auth_client, pdf_file):
        with patch("resumes.services.resume_service.upload_and_parse") as mock_parse:
            mock_parse.return_value = {"file_url": "/media/r.pdf", "parsed_data": PARSED_DATA}
            response = auth_client.post(
                "/api/v1/resumes/upload/",
                {"file": pdf_file, "name": "My CV"},
                format="multipart",
            )
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "resume_data" in data
        assert "original_file_url" in data
        assert "created_at" in data

    def test_upload_rejects_wrong_extension(self, auth_client):
        txt = SimpleUploadedFile("cv.txt", b"text", content_type="text/plain")
        response = auth_client.post(
            "/api/v1/resumes/upload/",
            {"file": txt},
            format="multipart",
        )
        assert response.status_code == 400

    def test_upload_rejects_oversized_file(self, auth_client, oversized_file):
        response = auth_client.post(
            "/api/v1/resumes/upload/",
            {"file": oversized_file},
            format="multipart",
        )
        assert response.status_code == 400

    def test_upload_without_file_returns_400(self, auth_client):
        response = auth_client.post("/api/v1/resumes/upload/", {}, format="multipart")
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# List endpoint — GET /api/v1/resumes/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestResumeListView:

    def test_requires_auth(self):
        response = APIClient().get("/api/v1/resumes/")
        assert response.status_code == 401

    def test_returns_only_own_resumes(self, auth_client, user, other_user):
        Resume.objects.create(user=user, name="Mine", resume_data={})
        Resume.objects.create(user=other_user, name="Not Mine", resume_data={})

        response = auth_client.get("/api/v1/resumes/")
        assert response.status_code == 200
        names = [r["name"] for r in response.json()]
        assert "Mine" in names
        assert "Not Mine" not in names

    def test_empty_list_for_new_user(self, auth_client):
        response = auth_client.get("/api/v1/resumes/")
        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_request(user):
    req = MagicMock()
    req.user = user
    return req
