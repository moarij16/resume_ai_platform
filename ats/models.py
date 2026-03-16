import uuid
from jobs.models import JobDescription
from resumes.models import Resume
from users.models import Users
from django.db import models


class ATSScan(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="scan_id"
    )

    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="ats_scans",
        db_column="user_id",
    )

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, db_column="resume_id")

    job = models.ForeignKey(
        JobDescription, on_delete=models.CASCADE, db_column="job_id"
    )

    ats_score = models.IntegerField()

    missing_keywords = models.JSONField(null=True, blank=True)

    suggestions = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "ats_scans"
