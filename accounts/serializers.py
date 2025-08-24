from __future__ import annotations

from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from phonenumber_field.serializerfields import PhoneNumberField

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Read-only user representation."""

    class Meta:
        model = User
        fields = ("id", "full_name", "email", "phone_number")
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    accept_terms = serializers.BooleanField(write_only=True)
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), message="This email is already registered."
            )
        ]
    )
    phone_number = PhoneNumberField(
        required=False,
        allow_null=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), message="This phone number is already registered."
            )
        ],
    )

    class Meta:
        model = User
        fields = (
            "id",
            "full_name",
            "email",
            "phone_number",
            "password",
            "password_confirm",
            "accept_terms",
        )
        read_only_fields = ("id",)

    def validate_accept_terms(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError("You must accept Terms.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        password = attrs.get("password")
        password_confirm = attrs.pop("password_confirm", None)
        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": ["Passwords do not match."]}
            )
        if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            raise serializers.ValidationError(
                {"password": ["Password must contain letters and numbers."]}
            )
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        validated_data.pop("accept_terms")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """Obtain JWT pair using email and password."""

    default_error_messages = {"no_active_account": "Invalid credentials"}

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        try:
            data = super().validate(attrs)
        except AuthenticationFailed as exc:  # pragma: no cover - handled by DRF
            raise AuthenticationFailed("Invalid credentials") from exc
        data["user"] = UserSerializer(self.user).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
