from core.base import BaseModel
import uuid
from users.models import Users
from django.db import models
from pgvector.django import VectorField


class JobDescription(BaseModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column="job_id",
    )

    user = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="job_descriptions"
    )

    job_title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)

    job_description_text = models.TextField()

    parsed_keywords = models.JSONField(null=True, blank=True)

    job_embedding = VectorField(dimensions=1536, null=True, blank=True)

    class Meta:
        db_table = "job_descriptions"

    def __str__(self):
        return f"{self.job_title} @ {self.company_name}"

    @classmethod
    def create_for_user(
        cls,
        user,
        job_title: str,
        company_name: str,
        job_description_text: str,
    ) -> "JobDescription":
        instance = cls(
            user=user,
            job_title=job_title,
            company_name=company_name,
            job_description_text=job_description_text,
        )
        instance.save()
        return instance

    def update_fields_from(self, **kwargs) -> None:
        allowed = {"job_title", "company_name", "job_description_text"}
        fields_to_update = []
        for field, value in kwargs.items():
            if field in allowed:
                setattr(self, field, value)
                fields_to_update.append(field)
        if fields_to_update:
            fields_to_update.append("updated_at")
            self.save(update_fields=fields_to_update)
