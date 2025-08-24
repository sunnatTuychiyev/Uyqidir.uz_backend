from __future__ import annotations

from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "is_active", "date_joined")
    search_fields = ("email", "full_name", "phone_number")
    ordering = ("-date_joined",)
