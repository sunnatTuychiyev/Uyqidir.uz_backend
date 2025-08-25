from __future__ import annotations

from django.apps import AppConfig


class ChatConfig(AppConfig):
    """Configuration for the chat application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "chat"
