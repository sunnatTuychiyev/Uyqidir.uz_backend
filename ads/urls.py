from __future__ import annotations

from rest_framework.routers import DefaultRouter

from .views import AdViewSet, AmenityViewSet, ModerationViewSet, MyAdViewSet

router = DefaultRouter()
router.register(r"ads", AdViewSet, basename="ad")
router.register(r"ads/my", MyAdViewSet, basename="my-ad")
router.register(r"ads/moderation", ModerationViewSet, basename="ad-moderation")
router.register(r"amenities", AmenityViewSet, basename="amenity")

urlpatterns = router.urls
