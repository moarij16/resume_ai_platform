from resumes.models import Resume
from users.models import Users
import uuid
from core.base import BaseModel
from django.db import models


class LinkedInBio(BaseModel):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column="linkedin_bio_id",
    )
    user = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="linkedin_bios"
    )
    resume = models.ForeignKey(
        Resume,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linkedin_bios",
    )
    document_content = models.TextField(blank=True)
    file_url = models.TextField(blank=True)

    class Meta:
        db_table = "linkedin_bios"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} — linkedin bio {self.id}"
