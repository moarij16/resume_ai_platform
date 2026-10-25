from rest_framework import serializers

from core.fields import OwnedResourceIdField
from jobs.models import JobDescription
from resumes.models import Resume
from .models import ATSScan


class ATSScanInputSerializer(serializers.Serializer):
    resume_id = OwnedResourceIdField(Resume, "Resume not found.")
    job_id = OwnedResourceIdField(
        JobDescription, "Job description not found.", required=False, allow_null=True
    )


class ATSScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ATSScan
        fields = [
            "id",
            "scan_mode",
            "ats_score",
            "breakdown",
            "missing_keywords",
            "suggestions",
            "scan_result",
            "resume",
            "job",
            "created_at",
        ]
        read_only_fields = fields
