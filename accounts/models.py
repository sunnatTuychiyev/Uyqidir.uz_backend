from __future__ import annotations

import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class UserManager(BaseUserManager):
    """Custom user manager."""

    def create_user(self, email: str, full_name: str, password: str | None = None, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, full_name: str, password: str, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, full_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Application user model using email as username."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.email
