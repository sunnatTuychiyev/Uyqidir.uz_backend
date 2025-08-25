from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class ChatTests(APITestCase):
    def setUp(self) -> None:
        self.user1 = User.objects.create_user(
            email="u1@example.com", full_name="User One", password="pass1234"
        )
        self.user2 = User.objects.create_user(
            email="u2@example.com", full_name="User Two", password="pass1234"
        )
        login = self.client.post(
            reverse("login"),
            {"email": "u1@example.com", "password": "pass1234"},
            format="json",
        )
        token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.chat_list_url = reverse("chat-list")

    def test_start_chat_and_send_message(self):
        resp = self.client.post(
            self.chat_list_url, {"user": str(self.user2.id)}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        chat_id = resp.data["id"]
        messages_url = reverse("chat-messages", args=[chat_id])
        resp_msg = self.client.post(
            messages_url, {"content": "Hello"}, format="json"
        )
        self.assertEqual(resp_msg.status_code, status.HTTP_201_CREATED)
        resp_list = self.client.get(messages_url)
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_list.data), 1)
        self.assertEqual(resp_list.data[0]["content"], "Hello")
