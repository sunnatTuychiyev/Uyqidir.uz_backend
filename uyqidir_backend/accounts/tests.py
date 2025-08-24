"""Tests for authentication API."""
from __future__ import annotations

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.me_url = reverse('me')
        self.logout_url = reverse('logout')
        self.refresh_url = reverse('token_refresh')

    def test_register_success(self):
        data = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'phone_number': '+998901112233',
            'password': 'StrongP4ss',
            'password_confirm': 'StrongP4ss',
            'accept_terms': True,
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_register_email_taken(self):
        User.objects.create_user(email='john@example.com', full_name='John Doe', password='StrongP4ss')
        data = {
            'full_name': 'Jane Doe',
            'email': 'john@example.com',
            'password': 'AnotherP4ss',
            'password_confirm': 'AnotherP4ss',
            'accept_terms': True,
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self):
        data = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'password': 'StrongP4ss',
            'password_confirm': 'WrongPass',
            'accept_terms': True,
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_terms_false(self):
        data = {
            'full_name': 'John Doe',
            'email': 'john@example.com',
            'password': 'StrongP4ss',
            'password_confirm': 'StrongP4ss',
            'accept_terms': False,
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success_and_fail(self):
        User.objects.create_user(email='john@example.com', full_name='John Doe', password='StrongP4ss')
        response = self.client.post(self.login_url, {'email': 'john@example.com', 'password': 'StrongP4ss'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        response_fail = self.client.post(self.login_url, {'email': 'john@example.com', 'password': 'wrong'}, format='json')
        self.assertEqual(response_fail.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_and_without_jwt(self):
        user = User.objects.create_user(email='john@example.com', full_name='John Doe', password='StrongP4ss')
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        # Without token
        response_no_token = self.client.get(self.me_url)
        self.assertEqual(response_no_token.status_code, status.HTTP_401_UNAUTHORIZED)

        # With token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], user.email)

    def test_logout_blacklists_token(self):
        user = User.objects.create_user(email='john@example.com', full_name='John Doe', password='StrongP4ss')
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        response = self.client.post(self.logout_url, {'refresh': str(refresh)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # Attempt to refresh with blacklisted token
        response_refresh = self.client.post(self.refresh_url, {'refresh': str(refresh)}, format='json')
        self.assertEqual(response_refresh.status_code, status.HTTP_401_UNAUTHORIZED)
