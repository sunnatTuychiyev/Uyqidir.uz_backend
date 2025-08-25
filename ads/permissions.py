from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Ad, AdStatus


class IsOwnerOrReadOnly(BasePermission):
    """Allow owners to modify their ads; others have read-only access."""

    def has_object_permission(self, request, view, obj: Ad) -> bool:
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        if obj.owner_id != getattr(request.user, "id", None):
            return False
        if request.method == "DELETE":
            return obj.status in {AdStatus.DRAFT, AdStatus.PENDING}
        if obj.status in {AdStatus.DRAFT, AdStatus.PENDING}:
            return True
        if obj.status == AdStatus.APPROVED and request.method in {"PUT", "PATCH"}:
            return True
        return False
