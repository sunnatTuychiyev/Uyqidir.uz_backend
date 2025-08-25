from __future__ import annotations

from rest_framework.routers import DefaultRouter

from .views import ChatThreadViewSet

router = DefaultRouter()
router.register(r"chats", ChatThreadViewSet, basename="chat")

urlpatterns = router.urls
