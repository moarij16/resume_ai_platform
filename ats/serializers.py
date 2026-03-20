from rest_framework import serializers
from .models import ATSScan


class ATSScanInputSerializer(serializers.Serializer):
    resume_id = serializers.UUIDField()
    job_id = serializers.UUIDField(required=False, allow_null=True)


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
