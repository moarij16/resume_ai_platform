from jobs.models import JobDescription
from importlib.metadata import version
from core.base import BaseModel
import uuid

from django.db import models

from users.models import Users


class Resume(BaseModel):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="resume_id"
    )
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="resumes",
        db_column="user_id",
    )
    name = models.CharField(max_length=255, db_column="resume_name")
    resume_version = models.IntegerField(default=1)
    resume_data = models.JSONField(null=True, blank=True)
    original_file_url = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "resumes"

    def __str__(self):
        return f"{self.name} - {self.user.email}"
