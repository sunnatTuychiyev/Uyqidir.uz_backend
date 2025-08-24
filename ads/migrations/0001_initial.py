from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Amenity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("slug", models.SlugField(max_length=120, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Ad",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("monthly_rent", models.PositiveIntegerField(help_text="UZS per month")),
                (
                    "property_type",
                    models.CharField(
                        choices=[
                            ("APARTMENT", "Apartment"),
                            ("HOUSE", "House"),
                            ("STUDIO", "Studio"),
                            ("COMMERCIAL", "Commercial"),
                        ],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("bedrooms", models.PositiveSmallIntegerField(default=0)),
                ("bathrooms", models.PositiveSmallIntegerField(default=0)),
                ("area_m2", models.DecimalField(decimal_places=2, max_digits=8)),
                ("address", models.CharField(max_length=255)),
                ("latitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("longitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("contact_name", models.CharField(blank=True, max_length=120)),
                ("contact_phone", phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, region=None)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("DRAFT", "Draft"),
                            ("PENDING", "Pending"),
                            ("APPROVED", "Approved"),
                            ("REJECTED", "Rejected"),
                            ("ARCHIVED", "Archived"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("moderation_note", models.TextField(blank=True)),
                ("slug", models.SlugField(max_length=220, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "amenities",
                    models.ManyToManyField(blank=True, to="ads.amenity"),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ads",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AdImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="ads/%Y/%m/%d/")),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "ad",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="ads.ad",
                    ),
                ),
            ],
            options={"unique_together": {("ad", "order")}},
        ),
        migrations.AddConstraint(
            model_name="ad",
            constraint=models.CheckConstraint(check=models.Q(("monthly_rent__gt", 0)), name="monthly_rent_gt_zero"),
        ),
        migrations.AddConstraint(
            model_name="ad",
            constraint=models.CheckConstraint(check=models.Q(("area_m2__gt", 0)), name="area_gt_zero"),
        ),
        migrations.AddConstraint(
            model_name="ad",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status__in", ["PENDING", "APPROVED"])),
                fields=("owner", "title"),
                name="uniq_owner_title_active",
            ),
        ),
        migrations.AddIndex(
            model_name="ad",
            index=models.Index(fields=["status"], name="ads_ad_status_idx"),
        ),
        migrations.AddIndex(
            model_name="ad",
            index=models.Index(fields=["property_type"], name="ads_ad_property_type_idx"),
        ),
        migrations.AddIndex(
            model_name="ad",
            index=models.Index(fields=["monthly_rent"], name="ads_ad_monthly_rent_idx"),
        ),
        migrations.AddIndex(
            model_name="ad",
            index=models.Index(fields=["created_at"], name="ads_ad_created_at_idx"),
        ),
    ]
