from __future__ import annotations

from rest_framework.throttling import UserRateThrottle


class AdPostRateThrottle(UserRateThrottle):
    """Limit ad creation to 10 per day per authenticated user."""

    scope = "ad_post"
