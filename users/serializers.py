from rest_framework import serializers
from .models import Users


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Users
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "created_at",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "email",
            "is_active",
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
