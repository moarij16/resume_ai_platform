from jobs.models import JobDescription
from importlib.metadata import version
from core.base import UserOwnedModel
import uuid

from django.db import models

from users.models import Users


class Resume(UserOwnedModel):
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

    @classmethod
    def create_from_upload(cls, user, file, name: str) -> "Resume":
        """
        Parse an uploaded resume file and persist the record.

        Args:
            user: Users instance.
            file: Django UploadedFile from request.FILES.
            name: Human-readable resume name.

        Returns:
            Saved Resume instance.

        Raises:
            ValueError: If the file cannot be parsed.
        """
        from resumes.services.resume_service import upload_and_parse

        result = upload_and_parse(user, file)
        resume = cls(
            user=user,
            name=name,
            resume_data=result["parsed_data"],
            original_file_url=result["file_url"],
        )
        resume.save()
        return resume

    def update_confirmed_data(self, name: str = None, resume_data: dict = None) -> None:
        """Update name and/or resume_data after user confirms the parsed output."""
        update_fields = ["updated_at"]
        if name is not None:
            self.name = name
            update_fields.append("name")
        if resume_data is not None:
            self.resume_data = resume_data
            update_fields.append("resume_data")
        self.save(update_fields=update_fields)
