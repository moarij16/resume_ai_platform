from rest_framework import serializers
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    is_pro = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "plan",
            "is_pro",
            "created_at",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "email",  # managed by Cognito — never updated here
            "plan",  # managed by billing — never updated here
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
        # delegate to model — serializer never touches fields directly
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.save(update_fields=["first_name", "last_name"])
        return instance
