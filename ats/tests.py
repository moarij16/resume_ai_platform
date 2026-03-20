"""
Tests for the ats app.

Covers:
  - ATSScan.create_for_user model factory
  - run_scan service — RESUME_ONLY and JD_MATCH modes
  - POST /api/v1/ats/scan/
  - GET  /api/v1/ats/history/
"""

import uuid
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from ats.models import ATSScan, ScanMode
from jobs.models import JobDescription
from resumes.models import Resume
from users.models import Users

SCAN_URL    = "/api/v1/ats/scan/"
HISTORY_URL = "/api/v1/ats/history/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    return Users.objects.create(
        supabase_uid=str(uuid.uuid4()),
        email="ats_user@example.com",
        first_name="ATS",
        last_name="Tester",
    )


@pytest.fixture
def other_user(db):
    return Users.objects.create(
        supabase_uid=str(uuid.uuid4()),
        email="other_ats@example.com",
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
        resume_data={"raw_text": "Software engineer with 5 years experience"},
    )


@pytest.fixture
def job(user):
    return JobDescription.create_for_user(
        user=user,
        job_title="Software Engineer",
        company_name="Acme",
        job_description_text="Python Django React experience required.",
    )


@pytest.fixture
def ats_scan(user, resume):
    return ATSScan.create_for_user(
        user=user,
        resume=resume,
        scan_mode=ScanMode.RESUME_ONLY,
        ats_score=75.0,
        breakdown={"section_completeness": 80},
        missing_keywords=[],
        suggestions=["Add more quantified achievements"],
        scan_result={"quality_score": 75.0},
    )


# Resume-only scorer mock result
RESUME_ONLY_RESULT = {
    "quality_score": 72.0,
    "section_completeness": 80,
    "keyword_strength": 65,
    "bullet_quality": 70,
    "format_compatibility": 90,
    "content_quantification": 55,
    "resume_length": "good",
    "recommendations": ["Quantify achievements", "Add a summary"],
}

# JD-match scorer mock result
JD_MATCH_RESULT = {
    "ats_score": 85.0,
    "breakdown": {"keyword_match": 88, "format": 82},
    "missing_critical_skills": ["Docker"],
    "recommendations": ["Add Docker experience"],
    "actionable_recommendations": [{"action": "Highlight Django projects"}],
}


# ---------------------------------------------------------------------------
# Model — ATSScan.create_for_user
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestATSScanCreateForUser:

    def test_creates_and_persists(self, user, resume):
        scan = ATSScan.create_for_user(
            user=user,
            resume=resume,
            scan_mode=ScanMode.RESUME_ONLY,
            ats_score=70.0,
            breakdown={},
            missing_keywords=[],
            suggestions=[],
            scan_result={},
        )
        assert scan.pk is not None
        assert ATSScan.objects.filter(pk=scan.pk).exists()

    def test_fields_are_set(self, user, resume):
        scan = ATSScan.create_for_user(
            user=user,
            resume=resume,
            scan_mode=ScanMode.RESUME_ONLY,
            ats_score=65.5,
            breakdown={"keyword_strength": 60},
            missing_keywords=["Python"],
            suggestions=["Add Python"],
            scan_result={"quality_score": 65.5},
        )
        assert scan.user == user
        assert scan.resume == resume
        assert scan.scan_mode == ScanMode.RESUME_ONLY
        assert scan.ats_score == 65.5
        assert scan.missing_keywords == ["Python"]

    def test_job_defaults_to_none(self, user, resume):
        scan = ATSScan.create_for_user(
            user=user, resume=resume, scan_mode=ScanMode.RESUME_ONLY,
            ats_score=70.0, breakdown={}, missing_keywords=[],
            suggestions=[], scan_result={},
        )
        assert scan.job is None

    def test_creates_with_job(self, user, resume, job):
        scan = ATSScan.create_for_user(
            user=user, resume=resume, job=job,
            scan_mode=ScanMode.JD_MATCH,
            ats_score=85.0, breakdown={}, missing_keywords=[],
            suggestions=[], scan_result={},
        )
        assert scan.job == job
        assert scan.scan_mode == ScanMode.JD_MATCH


# ---------------------------------------------------------------------------
# Service — run_scan
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRunScan:

    def test_resume_only_mode(self, user, resume):
        with patch("ats.services.ats_service.analyze_resume_quality") as mock_quality:
            mock_quality.return_value = RESUME_ONLY_RESULT
            from ats.services.ats_service import run_scan
            scan = run_scan(user=user, resume_id=resume.id)

        assert scan.scan_mode == ScanMode.RESUME_ONLY
        assert scan.ats_score == 72.0
        assert scan.job is None
        mock_quality.assert_called_once()

    def test_jd_match_mode(self, user, resume, job):
        with patch("ats.services.ats_service.score_resume_vs_jd") as mock_score:
            mock_score.return_value = JD_MATCH_RESULT
            from ats.services.ats_service import run_scan
            scan = run_scan(user=user, resume_id=resume.id, job_id=job.id)

        assert scan.scan_mode == ScanMode.JD_MATCH
        assert scan.ats_score == 85.0
        assert scan.job == job
        assert "Docker" in scan.missing_keywords
        mock_score.assert_called_once()

    def test_jd_match_collects_actionable_recommendations(self, user, resume, job):
        with patch("ats.services.ats_service.score_resume_vs_jd") as mock_score:
            mock_score.return_value = JD_MATCH_RESULT
            from ats.services.ats_service import run_scan
            scan = run_scan(user=user, resume_id=resume.id, job_id=job.id)

        assert "Highlight Django projects" in scan.suggestions

    def test_raises_if_resume_not_owned(self, user, other_user, resume):
        other_resume = Resume.objects.create(
            user=other_user, name="Other", resume_data={}
        )
        from ats.services.ats_service import run_scan
        with pytest.raises(Exception):
            run_scan(user=user, resume_id=other_resume.id)

    def test_scan_is_persisted(self, user, resume):
        with patch("ats.services.ats_service.analyze_resume_quality") as mock_quality:
            mock_quality.return_value = RESUME_ONLY_RESULT
            from ats.services.ats_service import run_scan
            scan = run_scan(user=user, resume_id=resume.id)

        assert ATSScan.objects.filter(pk=scan.pk).exists()


# ---------------------------------------------------------------------------
# Endpoint — POST /api/v1/ats/scan/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestATSScanEndpoint:

    def test_requires_auth(self, resume):
        response = APIClient().post(SCAN_URL, {"resume_id": str(resume.id)}, format="json")
        assert response.status_code == 401

    def test_resume_only_returns_201(self, auth_client, resume):
        with patch("ats.services.ats_service.analyze_resume_quality") as mock_q:
            mock_q.return_value = RESUME_ONLY_RESULT
            response = auth_client.post(SCAN_URL, {"resume_id": str(resume.id)}, format="json")
        assert response.status_code == 201

    def test_response_shape(self, auth_client, resume):
        with patch("ats.services.ats_service.analyze_resume_quality") as mock_q:
            mock_q.return_value = RESUME_ONLY_RESULT
            response = auth_client.post(SCAN_URL, {"resume_id": str(resume.id)}, format="json")
        data = response.json()
        for key in ("id", "scan_mode", "ats_score", "breakdown", "missing_keywords", "suggestions", "created_at"):
            assert key in data, f"missing key: {key}"

    def test_jd_match_scan(self, auth_client, resume, job):
        with patch("ats.services.ats_service.score_resume_vs_jd") as mock_s:
            mock_s.return_value = JD_MATCH_RESULT
            response = auth_client.post(
                SCAN_URL,
                {"resume_id": str(resume.id), "job_id": str(job.id)},
                format="json",
            )
        assert response.status_code == 201
        assert response.json()["scan_mode"] == ScanMode.JD_MATCH

    def test_missing_resume_id_returns_400(self, auth_client):
        response = auth_client.post(SCAN_URL, {}, format="json")
        assert response.status_code == 400

    def test_invalid_resume_id_returns_400(self, auth_client):
        with patch("ats.services.ats_service.analyze_resume_quality"):
            response = auth_client.post(
                SCAN_URL, {"resume_id": str(uuid.uuid4())}, format="json"
            )
        assert response.status_code == 400

    def test_cannot_scan_other_users_resume(self, auth_client, other_user):
        other_resume = Resume.objects.create(
            user=other_user, name="Other", resume_data={}
        )
        response = auth_client.post(
            SCAN_URL, {"resume_id": str(other_resume.id)}, format="json"
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Endpoint — GET /api/v1/ats/history/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestATSHistoryEndpoint:

    def test_requires_auth(self):
        response = APIClient().get(HISTORY_URL)
        assert response.status_code == 401

    def test_returns_own_scans_only(self, auth_client, user, other_user, resume):
        ATSScan.create_for_user(
            user=user, resume=resume, scan_mode=ScanMode.RESUME_ONLY,
            ats_score=70.0, breakdown={}, missing_keywords=[], suggestions=[], scan_result={},
        )
        other_resume = Resume.objects.create(user=other_user, name="Other", resume_data={})
        ATSScan.create_for_user(
            user=other_user, resume=other_resume, scan_mode=ScanMode.RESUME_ONLY,
            ats_score=50.0, breakdown={}, missing_keywords=[], suggestions=[], scan_result={},
        )
        response = auth_client.get(HISTORY_URL)
        assert response.status_code == 200
        scores = [s["ats_score"] for s in response.json()]
        assert 70.0 in scores
        assert 50.0 not in scores

    def test_empty_for_new_user(self, auth_client):
        response = auth_client.get(HISTORY_URL)
        assert response.status_code == 200
        assert response.json() == []

    def test_ordered_by_newest_first(self, auth_client, user, resume):
        s1 = ATSScan.create_for_user(
            user=user, resume=resume, scan_mode=ScanMode.RESUME_ONLY,
            ats_score=60.0, breakdown={}, missing_keywords=[], suggestions=[], scan_result={},
        )
        s2 = ATSScan.create_for_user(
            user=user, resume=resume, scan_mode=ScanMode.RESUME_ONLY,
            ats_score=80.0, breakdown={}, missing_keywords=[], suggestions=[], scan_result={},
        )
        response = auth_client.get(HISTORY_URL)
        ids = [s["id"] for s in response.json()]
        assert ids[0] == str(s2.pk)  # newest first
