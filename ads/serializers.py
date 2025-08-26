from __future__ import annotations

from typing import Any
import base64
import imghdr
import uuid

from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import Ad, AdImage, Amenity, AdStatus

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """A DRF ImageField for handling base64-encoded images."""

    def to_internal_value(self, data: Any) -> Any:
        if isinstance(data, str):
            if data.startswith("data:image"):
                header, data = data.split(";base64,", 1)
            try:
                decoded_file = base64.b64decode(data)
            except Exception as exc:  # pragma: no cover - defensive
                raise serializers.ValidationError("Invalid image data") from exc

            file_extension = imghdr.what(None, decoded_file)
            if not file_extension:
                raise serializers.ValidationError("Invalid image data")

            file_name = f"{uuid.uuid4().hex[:12]}.{file_extension}"
            data = ContentFile(decoded_file, name=file_name)

        return super().to_internal_value(data)


class AmenitySerializer(serializers.ModelSerializer):
    """Serializer for Amenity objects."""

    class Meta:
        model = Amenity
        fields = ["id", "name", "slug"]


class AdImageSerializer(serializers.ModelSerializer):
    """Serializer for ad images."""

    image = Base64ImageField()

    class Meta:
        model = AdImage
        fields = ["id", "image", "order", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        ad: Ad = self.context.get("ad")
        if ad and ad.images.count() >= 10 and not self.instance:
            raise serializers.ValidationError("Maximum of 10 images allowed per ad.")
        return attrs

    def create(self, validated_data: dict[str, Any]) -> AdImage:
        ad: Ad = self.context["ad"]
        validated_data.setdefault("order", ad.images.count())
        return AdImage.objects.create(ad=ad, **validated_data)


class AdCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer used for creating and updating ads."""

    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    amenities = serializers.PrimaryKeyRelatedField(
        queryset=Amenity.objects.all(), many=True, required=False
    )
    images = serializers.ListField(
        child=Base64ImageField(), write_only=True, required=False
    )

    class Meta:
        model = Ad
        fields = [
            "id",
            "title",
            "description",
            "monthly_rent",
            "property_type",
            "bedrooms",
            "bathrooms",
            "area_m2",
            "address",
            "latitude",
            "longitude",
            "amenities",
            "contact_name",
            "contact_phone",
            "images",
        ]
        read_only_fields = ["id"]

    def validate_monthly_rent(self, value: int) -> int:
        if not 1 <= value <= 1_000_000_000:
            raise serializers.ValidationError("Rent must be between 1 and 1,000,000,000 UZS.")
        return value

    def validate_bedrooms(self, value: int) -> int:
        if not 0 <= value <= 50:
            raise serializers.ValidationError("Bedrooms must be between 0 and 50.")
        return value

    def validate_bathrooms(self, value: int) -> int:
        if not 0 <= value <= 50:
            raise serializers.ValidationError("Bathrooms must be between 0 and 50.")
        return value

    def validate_area_m2(self, value: Any) -> Any:
        if not 1 <= float(value) <= 100_000:
            raise serializers.ValidationError("Area must be between 1 and 100000 square meters.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        attrs = super().validate(attrs)
        images = attrs.get("images", [])
        instance: Ad | None = getattr(self, "instance", None)
        existing = instance.images.count() if instance else 0
        if existing + len(images) > 10:
            raise serializers.ValidationError("Maximum of 10 images allowed per ad.")
        if ("latitude" in attrs) ^ ("longitude" in attrs):
            raise serializers.ValidationError(
                "Latitude and longitude must be provided together."
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> Ad:
        images = validated_data.pop("images", [])
        amenities = validated_data.pop("amenities", [])
        request = self.context["request"]
        user = request.user

        if not validated_data.get("contact_name"):
            validated_data["contact_name"] = getattr(user, "full_name", "")
        if not validated_data.get("contact_phone"):
            phone = getattr(user, "phone_number", "")
            # Ensure a blank string is stored instead of None to satisfy NOT NULL
            validated_data["contact_phone"] = phone or ""

        ad = Ad.objects.create(owner=user, status=AdStatus.PENDING, **validated_data)
        if amenities:
            ad.amenities.set(amenities)
        self._create_images(ad, images)
        return ad

    @transaction.atomic
    def update(self, instance: Ad, validated_data: dict[str, Any]) -> Ad:
        if instance.status == AdStatus.APPROVED:
            allowed = {"monthly_rent", "contact_phone"}
            invalid = [f for f in validated_data.keys() if f not in allowed]
            if invalid:
                raise serializers.ValidationError(
                    "Only price and contact phone can be updated once approved."
                )
        images = validated_data.pop("images", [])
        amenities = validated_data.pop("amenities", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if amenities is not None:
            instance.amenities.set(amenities)
        if images:
            self._create_images(instance, images)
        return instance

    def _create_images(self, ad: Ad, images: list) -> None:
        objects = [AdImage(ad=ad, image=img, order=i) for i, img in enumerate(images, start=ad.images.count())]
        if objects:
            AdImage.objects.bulk_create(objects)


class AdDetailSerializer(serializers.ModelSerializer):
    """Read-only serializer for ad details."""

    amenities = AmenitySerializer(many=True, read_only=True)
    images = AdImageSerializer(many=True, read_only=True)
    owner = serializers.SerializerMethodField()

    class Meta:
        model = Ad
        fields = [
            "id",
            "slug",
            "status",
            "owner",
            "title",
            "description",
            "monthly_rent",
            "property_type",
            "bedrooms",
            "bathrooms",
            "area_m2",
            "address",
            "latitude",
            "longitude",
            "amenities",
            "contact_name",
            "contact_phone",
            "images",
            "is_active",
            "created_at",
            "updated_at",
            "moderation_note",
        ]

    def get_owner(self, obj: Ad) -> dict[str, Any]:
        owner = obj.owner
        active_ads = owner.ads.filter(
            status=AdStatus.APPROVED, is_active=True
        ).count()
        return {
            "id": str(owner.pk),
            "username": getattr(owner, "email", ""),
            "full_name": getattr(owner, "full_name", ""),
            "active_ads": active_ads,
        }
