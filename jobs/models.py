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
