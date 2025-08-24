"""Serializers for accounts app."""
from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for reading user information."""

    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'phone_number')
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    accept_terms = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = ('full_name', 'email', 'phone_number', 'password', 'password_confirm', 'accept_terms')

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value

    def validate_phone_number(self, value: Any) -> Any:
        if value and User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('This phone number is already registered.')
        return value

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
            raise serializers.ValidationError('Password must contain letters and numbers.')
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        if not attrs.get('accept_terms'):
            raise serializers.ValidationError({'accept_terms': 'You must accept Terms.'})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        validated_data.pop('password_confirm')
        validated_data.pop('accept_terms')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        user = authenticate(username=attrs.get('email'), password=attrs.get('password'))
        if not user:
            raise AuthenticationFailed('Invalid credentials')
        attrs['user'] = user
        return attrs


class LoginResponseSerializer(serializers.Serializer):
    """Response serializer for login endpoint."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
