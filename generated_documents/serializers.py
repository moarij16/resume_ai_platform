from rest_framework import serializers

from resumes.models import Resume
from jobs.models import JobDescription
from core.ai.prompts.config import Tone
from core.fields import OwnedResourceIdField
from .models import GeneratedDocument

# TONE_CHOICES = Tone.ALL
# LENGTH_CHOICES = ["brief", "standard", "detailed"]


class GeneratedDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedDocument
        fields = [
            "id",
            "document_type",
            "document_content",
            "file_url",
            "resume",
            "job",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CoverLetterInputSerializer(serializers.Serializer):
    resume_id = OwnedResourceIdField(Resume, "Resume not found.")
    job_id = OwnedResourceIdField(
        JobDescription, "Job description not found.", required=False, allow_null=True
    )
    # tone = serializers.ChoiceField(choices=TONE_CHOICES, default=Tone.PROFESSIONAL)
    # custom_instructions = serializers.CharField(required=False, default="", allow_blank=True)
    # focus_areas = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    # length = serializers.ChoiceField(choices=LENGTH_CHOICES, default="standard")
    # industry = serializers.CharField(required=False, default="", allow_blank=True)


class LinkedInBioInputSerializer(serializers.Serializer):
    resume_id = OwnedResourceIdField(Resume, "Resume not found.")
    # tone = serializers.ChoiceField(choices=TONE_CHOICES, default=Tone.PROFESSIONAL)
    # custom_instructions = serializers.CharField(required=False, default="", allow_blank=True)
    # focus_areas = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class ResumeRefactorInputSerializer(serializers.Serializer):
    resume_id = OwnedResourceIdField(Resume, "Resume not found.")
    job_id = OwnedResourceIdField(
        JobDescription, "Job description not found.", required=False, allow_null=True
    )
    # tone = serializers.ChoiceField(choices=TONE_CHOICES, default=Tone.PROFESSIONAL)
    # custom_instructions = serializers.CharField(required=False, default="", allow_blank=True)
    # focus_areas = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class ResumeGenerateSerializer(serializers.Serializer):
    resume_id = OwnedResourceIdField(Resume, "Resume not found.")
    job_id = OwnedResourceIdField(
        JobDescription, "Job description not found.", required=False, allow_null=True
    )
    # tone = serializers.ChoiceField(choices=TONE_CHOICES, default=Tone.PROFESSIONAL)
    # custom_instructions = serializers.CharField(required=False, default="", allow_blank=True)
    # focus_areas = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    # length = serializers.ChoiceField(choices=LENGTH_CHOICES, default="standard")
    # industry = serializers.CharField(required=False, default="", allow_blank=True)
