from rest_framework import serializers

from .models import JobDescription


class JobDescriptionCreateSerializer(serializers.Serializer):
    job_title = serializers.CharField(max_length=255)
    company_name = serializers.CharField(max_length=255)
    job_description_text = serializers.CharField()

    def create(self, validated_data):
        user = self.context["request"].user
        return JobDescription.create_for_user(user=user, **validated_data)

    def update(self, instance, validated_data):
        raise NotImplementedError


class JobDescriptionUpdateSerializer(serializers.Serializer):
    job_title = serializers.CharField(max_length=255, required=False)
    company_name = serializers.CharField(max_length=255, required=False)
    job_description_text = serializers.CharField(required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one field must be provided.")
        return attrs

    def update(self, instance, validated_data):
        instance.update_fields_from(**validated_data)
        return instance

    def create(self, validated_data):
        raise NotImplementedError


class JobDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDescription
        fields = [
            "id",
            "job_title",
            "company_name",
            "job_description_text",
            "parsed_keywords",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
