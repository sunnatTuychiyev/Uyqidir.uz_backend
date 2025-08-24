from __future__ import annotations

from django.apps import AppConfig


class AdsConfig(AppConfig):
    """Configuration for the ads application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "ads"

    def ready(self) -> None:  # pragma: no cover - import signals
        import ads.signals  # noqa: F401
