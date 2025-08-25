from __future__ import annotations

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ads.models import Ad
from .models import ChatMessage, ChatThread

User = get_user_model()


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serialize chat messages."""

    sender = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ["id", "sender", "content", "created_at"]


class ChatThreadSerializer(serializers.ModelSerializer):
    """Serialize chat threads."""

    participants = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    ad = serializers.PrimaryKeyRelatedField(read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatThread
        fields = ["id", "ad", "participants", "created_at", "last_message"]

    @extend_schema_field(ChatMessageSerializer)
    def get_last_message(self, obj: ChatThread):
        msg = obj.messages.order_by("-created_at").first()
        return ChatMessageSerializer(msg).data if msg else None


class ChatThreadCreateSerializer(serializers.Serializer):
    """Validate data for starting a chat thread."""

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    ad = serializers.PrimaryKeyRelatedField(queryset=Ad.objects.all(), required=False, allow_null=True)
