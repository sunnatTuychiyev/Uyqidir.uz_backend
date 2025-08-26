from __future__ import annotations

from decimal import Decimal

from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from .filters import AdFilter
from .models import Ad, AdStatus, Amenity
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    AdCreateUpdateSerializer,
    AdDetailSerializer,
    AdImageSerializer,
    AmenitySerializer,
)
from .throttles import AdPostRateThrottle


class AdViewSet(viewsets.ModelViewSet):
    """Public advertisement endpoints."""

    queryset = Ad.objects.select_related("owner").prefetch_related("amenities", "images")
    serializer_class = AdDetailSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AdFilter
    search_fields = ["title", "description", "address"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny(), IsOwnerOrReadOnly()]
        return [IsAuthenticated(), IsOwnerOrReadOnly()]

    def get_queryset(self):
        qs = Ad.objects.select_related("owner").prefetch_related("amenities", "images")
        if self.action == "list":
            qs = qs.filter(is_active=True)
            if self.request.user.is_staff:
                return qs
            if self.request.user.is_authenticated:
                return qs.filter(Q(status=AdStatus.APPROVED) | Q(owner=self.request.user))
            return qs
        if self.action == "retrieve":
            if self.request.user.is_authenticated:
                if self.request.user.is_staff:
                    return qs
                return qs.filter(Q(status=AdStatus.APPROVED, is_active=True) | Q(owner=self.request.user))
            return qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return AdCreateUpdateSerializer
        if self.action in {"images", "delete_image"}:
            return AdImageSerializer
        return AdDetailSerializer

    def get_throttles(self):
        if self.action == "create":
            return [AdPostRateThrottle()]
        return []

    @extend_schema(
        request=AdCreateUpdateSerializer,
        responses=AdDetailSerializer,
        examples=[
            OpenApiExample(
                "Ad creation",
                media_type="multipart/form-data",
                value={
                    "title": "Spacious 2-Bedroom Apartment",
                    "description": "...",
                    "monthly_rent": 4500000,
                    "property_type": "APARTMENT",
                    "bedrooms": 2,
                    "bathrooms": 1,
                    "area_m2": "65.00",
                    "address": "Yakkasaroy, Tashkent",
                    "latitude": "41.3111",
                    "longitude": "69.2797",
                    "amenities": [1, 3],
                    "contact_name": "Ali",
                    "contact_phone": "+998901234567",
                    "images": ["(binary)", "(binary)"],
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_destroy(self, instance: Ad) -> None:
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])

    @action(detail=True, methods=["post"], serializer_class=AdImageSerializer)
    def images(self, request, pk=None):
        ad = self.get_object()
        serializer = AdImageSerializer(data=request.data, context={"ad": ad})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "image_id", OpenApiTypes.INT, OpenApiParameter.PATH
            )
        ]
    )
    @action(detail=True, methods=["delete"], url_path="images/(?P<image_id>[^/.]+)")
    def delete_image(self, request, pk=None, image_id=None):
        ad = self.get_object()
        image = get_object_or_404(ad.images, pk=image_id)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        ad = self.get_object()
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        ad.status = AdStatus.APPROVED
        ad.moderation_note = request.data.get("moderation_note", "")
        ad.save(update_fields=["status", "moderation_note", "updated_at"])
        return Response(AdDetailSerializer(ad, context={"request": request}).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        ad = self.get_object()
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        note = request.data.get("moderation_note")
        if not note:
            return Response({"moderation_note": ["This field is required."]}, status=400)
        ad.status = AdStatus.REJECTED
        ad.moderation_note = note
        ad.save(update_fields=["status", "moderation_note", "updated_at"])
        return Response(AdDetailSerializer(ad, context={"request": request}).data)

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        qs = Ad.objects.filter(is_active=True)
        counts = (
            qs.values("status")
            .filter(
                status__in=[
                    AdStatus.APPROVED,
                    AdStatus.PENDING,
                    AdStatus.ARCHIVED,
                ]
            )
            .annotate(total=Count("id"))
        )
        data = {"available": 0, "pending": 0, "rented": 0}
        for item in counts:
            if item["status"] == AdStatus.APPROVED:
                data["available"] = item["total"]
            elif item["status"] == AdStatus.PENDING:
                data["pending"] = item["total"]
            elif item["status"] == AdStatus.ARCHIVED:
                data["rented"] = item["total"]
        data["total"] = sum(data.values())
        return Response(data)

    @action(detail=False, methods=["get"], url_path="nearby")
    def nearby(self, request):
        try:
            lat = Decimal(request.query_params.get("lat"))
            lng = Decimal(request.query_params.get("lng"))
            radius = Decimal(request.query_params.get("radius_km", "5"))
        except (TypeError, ValueError):
            return Response({"detail": "Invalid coordinates."}, status=400)
        delta = radius / Decimal("111")
        qs = self.get_queryset().filter(
            latitude__range=(lat - delta, lat + delta),
            longitude__range=(lng - delta, lng + delta),
        )
        page = self.paginate_queryset(qs)
        serializer = AdDetailSerializer(page or qs, many=True, context={"request": request})
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="similar")
    def similar(self, request, pk=None):
        ad = self.get_object()
        qs = (
            Ad.objects.filter(
                property_type=ad.property_type,
                status=AdStatus.APPROVED,
                is_active=True,
            )
            .exclude(id=ad.id)
            .order_by("-created_at")[:3]
        )
        serializer = AdDetailSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class MyAdViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Endpoints for the current user's ads."""

    serializer_class = AdDetailSerializer
    throttle_classes: list = []
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AdFilter
    search_fields = ["title", "description", "address"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny(), IsOwnerOrReadOnly()]
        return [IsAuthenticated(), IsOwnerOrReadOnly()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Ad.objects.none()
        return Ad.objects.filter(owner=self.request.user).select_related("owner").prefetch_related(
            "amenities", "images"
        )

    def get_serializer_class(self):
        if self.action in {"update", "partial_update"}:
            return AdCreateUpdateSerializer
        return AdDetailSerializer

    def perform_destroy(self, instance: Ad) -> None:
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class ModerationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """List pending ads for moderation."""

    queryset = Ad.objects.filter(status=AdStatus.PENDING).select_related("owner").prefetch_related(
        "amenities", "images"
    )
    serializer_class = AdDetailSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes: list = []

    def list(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().list(request, *args, **kwargs)


class AmenityViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoints for amenities."""

    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    throttle_classes: list = []
