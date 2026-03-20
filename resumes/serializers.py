from pathlib import Path

from django.conf import settings
from rest_framework import serializers

from .models import Resume


class ResumeUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    name = serializers.CharField(max_length=255, required=False)

    def validate_file(self, value):
        ext = Path(value.name).suffix.lower()
        if ext not in (".pdf", ".docx"):
            raise serializers.ValidationError("Only PDF and DOCX files are supported.")
        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 5 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError("File size exceeds the 5 MB limit.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        file = validated_data["file"]
        name = validated_data.get("name") or Path(file.name).stem
        return Resume.create_from_upload(user, file, name)

    def update(self, instance, validated_data):
        raise NotImplementedError


class ResumeUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    resume_data = serializers.JSONField(required=False)

    def update(self, instance, validated_data):
        instance.update_confirmed_data(
            name=validated_data.get("name"),
            resume_data=validated_data.get("resume_data"),
        )
        return instance


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = [
            "id",
            "name",
            "resume_version",
            "resume_data",
            "original_file_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
