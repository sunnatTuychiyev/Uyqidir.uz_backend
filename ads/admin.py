from __future__ import annotations

from django.contrib import admin

from .models import Ad, AdImage, Amenity


class AdImageInline(admin.TabularInline):
    model = AdImage
    extra = 1


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "property_type", "monthly_rent", "created_at")
    list_filter = ("status", "property_type", "created_at")
    search_fields = ("title", "address")
    inlines = [AdImageInline]


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
