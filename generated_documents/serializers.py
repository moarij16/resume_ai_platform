from rest_framework import serializers

from resumes.models import Resume
from jobs.models import JobDescription
from core.ai.prompts.config import Tone
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
    resume_id = serializers.UUIDField()
    job_id = serializers.UUIDField(required=False)
    # tone = serializers.ChoiceField(choices=TONE_CHOICES, default=Tone.PROFESSIONAL)
    # custom_instructions = serializers.CharField(required=False, default="", allow_blank=True)
    # focus_areas = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    # length = serializers.ChoiceField(choices=LENGTH_CHOICES, default="standard")
    # industry = serializers.CharField(required=False, default="", allow_blank=True)

    def validate_resume_id(self, value):
        user = self.context["request"].user
        if not Resume.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Resume not found.")
        return value

    def validate_job_id(self, value):
        if value is None:
            return value
        user = self.context["request"].user
        if not JobDescription.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Job description not found.")
        return value


class LinkedInBioInputSerializer(serializers.Serializer):
    resume_id = serializers.UUIDField()
    # tone = serializers.ChoiceField(choices=TONE_CHOICES, default=Tone.PROFESSIONAL)
    # custom_instructions = serializers.CharField(required=False, default="", allow_blank=True)
    # focus_areas = serializers.ListField(child=serializers.CharField(), required=False, default=list)

    def validate_resume_id(self, value):
        user = self.context["request"].user
        if not Resume.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Resume not found.")
        return value


class ResumeRefactorInputSerializer(serializers.Serializer):
    resume_id = serializers.UUIDField()
    job_id = serializers.UUIDField(required=False)
    # tone = serializers.ChoiceField(choices=TONE_CHOICES, default=Tone.PROFESSIONAL)
    # custom_instructions = serializers.CharField(required=False, default="", allow_blank=True)
    # focus_areas = serializers.ListField(child=serializers.CharField(), required=False, default=list)

    def validate_resume_id(self, value):
        user = self.context["request"].user
        if not Resume.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Resume not found.")
        return value

    def validate_job_id(self, value):
        if value is None:
            return value
        user = self.context["request"].user
        if not JobDescription.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Job description not found.")
        return value


class ResumeGenerateSerializer(serializers.Serializer):
    resume_id = serializers.UUIDField()
    job_id = serializers.UUIDField(required=False)
    # tone = serializers.ChoiceField(choices=TONE_CHOICES, default=Tone.PROFESSIONAL)
    # custom_instructions = serializers.CharField(required=False, default="", allow_blank=True)
    # focus_areas = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    # length = serializers.ChoiceField(choices=LENGTH_CHOICES, default="standard")
    # industry = serializers.CharField(required=False, default="", allow_blank=True)

    def validate_resume_id(self, value):
        user = self.context["request"].user
        if not Resume.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Resume not found.")
        return value

    def validate_job_id(self, value):
        if value is None:
            return value
        user = self.context["request"].user
        if not JobDescription.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Job description not found.")
        return value
