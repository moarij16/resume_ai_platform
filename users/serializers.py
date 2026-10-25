from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

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


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=100, required=False, default="")
    last_name = serializers.CharField(max_length=100, required=False, default="")

    def validate_email(self, value):
        value = value.strip().lower()
        if Users.email_taken(value):
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return value

    def validate(self, data):
        candidate = Users(
            email=data["email"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
        )
        validate_password(data["password"], user=candidate)
        return data

    def create(self, validated_data):
        return Users.register(**validated_data)

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            "user": UserSerializer(instance).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class LoginSerializer(TokenObtainPairSerializer):
    """Email + password -> access/refresh tokens."""

    def validate(self, attrs):
        attrs[self.username_field] = attrs[self.username_field].strip().lower()
        data = super().validate(attrs)
        self.user.record_login()
        data["user"] = UserSerializer(self.user).data
        return data


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        if not self.instance.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value, user=self.instance)
        return value

    def update(self, instance, validated_data):
        instance.change_password(validated_data["new_password"])
        return instance


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        try:
            return RefreshToken(value)
        except TokenError:
            raise serializers.ValidationError("Invalid or expired refresh token.")

    def save(self, **kwargs):
        self.validated_data["refresh"].blacklist()
