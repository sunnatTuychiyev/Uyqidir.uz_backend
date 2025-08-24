from __future__ import annotations

import django_filters

from .models import Ad, Amenity


class AdFilter(django_filters.FilterSet):
    """FilterSet for ads listing."""

    min_price = django_filters.NumberFilter(field_name="monthly_rent", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="monthly_rent", lookup_expr="lte")
    min_area = django_filters.NumberFilter(field_name="area_m2", lookup_expr="gte")
    max_area = django_filters.NumberFilter(field_name="area_m2", lookup_expr="lte")
    amenities = django_filters.ModelMultipleChoiceFilter(
        queryset=Amenity.objects.all(), to_field_name="id"
    )

    class Meta:
        model = Ad
        fields = [
            "property_type",
            "bedrooms",
            "bathrooms",
            "amenities",
        ]
