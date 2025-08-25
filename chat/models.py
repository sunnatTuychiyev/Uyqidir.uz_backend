from __future__ import annotations

from django.conf import settings
from django.db import models


class ChatThread(models.Model):
    """Conversation between two users about an optional advertisement."""

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="chat_threads"
    )
    ad = models.ForeignKey(
        "ads.Ad",
        on_delete=models.CASCADE,
        related_name="chat_threads",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"Thread {self.pk}"

    def has_participant(self, user) -> bool:
        """Return True if the user is part of this thread."""
        return self.participants.filter(pk=user.pk).exists()


class ChatMessage(models.Model):
    """Message sent within a chat thread."""

    thread = models.ForeignKey(
        ChatThread, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"Message {self.pk} in thread {self.thread_id}"
