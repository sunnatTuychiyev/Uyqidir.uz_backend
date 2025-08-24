from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthTests(APITestCase):
    def setUp(self) -> None:
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.me_url = reverse("me")
        self.refresh_url = reverse("token_refresh")
        self.logout_url = reverse("logout")

    def register_user(self, **kwargs):
        data = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone_number": "+998901112233",
            "password": "StrongPass123",
            "password_confirm": "StrongPass123",
            "accept_terms": True,
        }
        data.update(kwargs)
        return self.client.post(self.register_url, data, format="json")

    def test_register_success(self):
        resp = self.register_user()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_register_email_taken(self):
        self.register_user()
        resp = self.register_user()
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", resp.data)

    def test_register_password_mismatch(self):
        resp = self.register_user(password_confirm="Mismatch123")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", resp.data)

    def test_register_terms_false(self):
        resp = self.register_user(accept_terms=False)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("accept_terms", resp.data)

    def test_login_success_and_fail(self):
        self.register_user()
        resp = self.client.post(
            self.login_url,
            {"email": "john@example.com", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        resp_fail = self.client.post(
            self.login_url,
            {"email": "john@example.com", "password": "wrong"},
            format="json",
        )
        self.assertEqual(resp_fail.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_auth(self):
        self.register_user()
        resp = self.client.get(self.me_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        login = self.client.post(
            self.login_url,
            {"email": "john@example.com", "password": "StrongPass123"},
            format="json",
        )
        token = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp2 = self.client.get(self.me_url)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertEqual(resp2.data["email"], "john@example.com")

    def test_logout_blacklists_token(self):
        self.register_user()
        login = self.client.post(
            self.login_url,
            {"email": "john@example.com", "password": "StrongPass123"},
            format="json",
        )
        refresh = login.data["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        resp = self.client.post(self.logout_url, {"refresh": refresh}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_205_RESET_CONTENT)
        resp2 = self.client.post(self.refresh_url, {"refresh": refresh}, format="json")
        self.assertEqual(resp2.status_code, status.HTTP_401_UNAUTHORIZED)
