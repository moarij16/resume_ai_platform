import uuid
from core.base import BaseModel
from django.db import models

from jobs.models import JobDescription
from resumes.models import Resume
from users.models import Users


class DocumentType(models.TextChoices):
    RESUME = "resume", "Resume"
    COVER_LETTER = "cover_letter", "Cover Letter"
    LINKED_IN_BIO = "linkedin_bio", "LinkedIn Bio"
    RESUME_REFACTOR = "resume_refactor", "Resume Refactor"


# Create your models here.
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
