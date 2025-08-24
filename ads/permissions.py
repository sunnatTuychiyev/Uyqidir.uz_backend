from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Ad


class IsOwnerOrReadOnly(BasePermission):
    """Allow owners to modify their ads; others have read-only access."""

    def has_object_permission(self, request, view, obj: Ad) -> bool:
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        return getattr(obj, "owner_id", None) == getattr(request.user, "id", None)
