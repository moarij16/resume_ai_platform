from rest_framework import serializers
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    is_premium = serializers.BooleanField(read_only=True)
    is_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "plan",
            "is_premium",
            "is_admin",
            "resume_improvements_used",
            "cover_letters_used",
            "ats_scans_used",
            "created_at",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "email",
            "role",
            "plan",
            "resume_improvements_used",
            "cover_letters_used",
            "ats_scans_used",
            "created_at",
            "last_login",
        ]

    def validate_first_name(self, value):
        value = value.strip()
        if len(value) > 100:
            raise serializers.ValidationError(
                "First name cannot exceed 100 characters."
            )
        return value

    def validate_last_name(self, value):
        value = value.strip()
        if len(value) > 100:
            raise serializers.ValidationError("Last name cannot exceed 100 characters.")
        return value

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.save(update_fields=["first_name", "last_name"])
        return instance
