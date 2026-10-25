import uuid
from django.db import models
from core.base import UserOwnedModel
from users.models import Users


class ScanMode(models.TextChoices):
    RESUME_ONLY = "resume_only", "Resume Only"
    JD_MATCH = "jd_match", "JD Match"


class ATSScan(UserOwnedModel):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="scan_id"
    )
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="ats_scans",
        db_column="user_id",
    )
    resume = models.ForeignKey(
        "resumes.Resume", on_delete=models.CASCADE, db_column="resume_id"
    )
    job = models.ForeignKey(
        "jobs.JobDescription",
        on_delete=models.CASCADE,
        db_column="job_id",
        null=True,
        blank=True,
    )
    scan_mode = models.CharField(
        max_length=20,
        choices=ScanMode.choices,
        default=ScanMode.RESUME_ONLY,
    )
    ats_score = models.FloatField()
    breakdown = models.JSONField(null=True, blank=True)
    missing_keywords = models.JSONField(null=True, blank=True)
    suggestions = models.JSONField(null=True, blank=True)
    scan_result = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "ats_scans"

    @classmethod
    def create_for_user(
        cls,
        user,
        resume,
        scan_mode: str,
        ats_score: float,
        breakdown: dict,
        missing_keywords: list,
        suggestions: list,
        scan_result: dict,
        job=None,
    ) -> "ATSScan":
        instance = cls(
            user=user,
            resume=resume,
            job=job,
            scan_mode=scan_mode,
            ats_score=ats_score,
            breakdown=breakdown,
            missing_keywords=missing_keywords,
            suggestions=suggestions,
            scan_result=scan_result,
        )
        instance.save()
        return instance
