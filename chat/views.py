from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ChatMessage, ChatThread
from .serializers import (
    ChatMessageSerializer,
    ChatThreadCreateSerializer,
    ChatThreadSerializer,
)


class ChatThreadViewSet(viewsets.ModelViewSet):
    """Manage chat threads for the authenticated user."""

    serializer_class = ChatThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatThread.objects.filter(participants=self.request.user).prefetch_related(
            "participants", "messages"
        )

    def create(self, request, *args, **kwargs):  # type: ignore[override]
        serializer = ChatThreadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        other_user = serializer.validated_data["user"]
        ad = serializer.validated_data.get("ad")
        thread = (
            ChatThread.objects.filter(ad=ad)
            .filter(participants=request.user)
            .filter(participants=other_user)
            .first()
        )
        created = False
        if not thread:
            thread = ChatThread.objects.create(ad=ad)
            thread.participants.add(request.user, other_user)
            created = True
        data = ChatThreadSerializer(thread).data
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=["get", "post"], serializer_class=ChatMessageSerializer)
    def messages(self, request, pk=None):
        thread = self.get_object()
        if request.method == "GET":
            serializer = ChatMessageSerializer(thread.messages.all(), many=True)
            return Response(serializer.data)
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(thread=thread, sender=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
