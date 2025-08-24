from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from phonenumber_field.modelfields import PhoneNumberField


class Amenity(models.Model):
    """Property amenity such as elevator, parking, etc."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.name


class PropertyType(models.TextChoices):
    """Available types of properties."""

    APARTMENT = "APARTMENT", "Apartment"
    HOUSE = "HOUSE", "House"
    STUDIO = "STUDIO", "Studio"
    COMMERCIAL = "COMMERCIAL", "Commercial"


class AdStatus(models.TextChoices):
    """Moderation status of an Ad."""

    DRAFT = "DRAFT", "Draft"
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    ARCHIVED = "ARCHIVED", "Archived"


class Ad(models.Model):
    """Classified advertisement for property rentals."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ads"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    monthly_rent = models.PositiveIntegerField(help_text="UZS per month")
    property_type = models.CharField(
        max_length=20, choices=PropertyType.choices, db_index=True
    )
    bedrooms = models.PositiveSmallIntegerField(default=0)
    bathrooms = models.PositiveSmallIntegerField(default=0)
    area_m2 = models.DecimalField(max_digits=8, decimal_places=2)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    amenities = models.ManyToManyField(Amenity, blank=True)
    contact_name = models.CharField(max_length=120, blank=True)
    contact_phone = PhoneNumberField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=AdStatus.choices,
        default=AdStatus.PENDING,
        db_index=True,
    )
    moderation_note = models.TextField(blank=True)
    slug = models.SlugField(max_length=220, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["property_type"]),
            models.Index(fields=["monthly_rent"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(monthly_rent__gt=0), name="monthly_rent_gt_zero"
            ),
            models.CheckConstraint(check=Q(area_m2__gt=0), name="area_gt_zero"),
            models.UniqueConstraint(
                fields=["owner", "title"],
                condition=Q(status__in=[AdStatus.PENDING, AdStatus.APPROVED]),
                name="uniq_owner_title_active",
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.title


class AdImage(models.Model):
    """Image associated with an advertisement."""

    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="ads/%Y/%m/%d/")
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("ad", "order")

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"Image {self.pk} for {self.ad_id}"

    def clean(self) -> None:
        """Ensure an ad does not have more than 10 images."""
        if self.ad.images.exclude(pk=self.pk).count() >= 10:
            raise ValidationError("An ad cannot have more than 10 images.")
