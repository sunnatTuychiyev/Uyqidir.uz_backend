from __future__ import annotations

from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from .models import Ad, AdImage


@receiver(pre_save, sender=Ad)
def set_ad_slug(sender, instance: Ad, **kwargs) -> None:
    """Generate a unique slug from the title if not provided."""
    if not instance.slug:
        base = slugify(instance.title)[:180]
        instance.slug = f"{base}-{uuid4().hex[:6]}"


@receiver(pre_save, sender=AdImage)
def limit_images(sender, instance: AdImage, **kwargs) -> None:
    """Ensure no more than 10 images are attached to an ad."""
    if instance.ad_id and instance.ad.images.exclude(pk=instance.pk).count() >= 10:
        raise ValidationError("An ad cannot have more than 10 images.")
