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


class DocumentType(models.TextChoices):
    RESUME = "resume", "Resume"
    COVER_LETTER = "cover_letter", "Cover Letter"
    LINKED_IN_BIO = "linkedin_bio", "LinkedIn Bio"
    RESUME_REFACTOR = "resume_refactor", "Resume Refactor"


class GeneratedDocument(BaseModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column="document_id",
    )

    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="generated_documents",
        db_column="user_id",
    )

    resume = models.ForeignKey(
        Resume,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_documents",
        db_column="resume_id",
    )

    job = models.ForeignKey(
        JobDescription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="job_id",
    )

    document_type = models.CharField(max_length=50, choices=DocumentType.choices)

    document_content = models.TextField()

    file_url = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "generated_documents"
