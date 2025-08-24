"""Views for authentication endpoints."""
from __future__ import annotations

from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    LoginSerializer,
    LoginResponseSerializer,
)


class RegisterView(APIView):
    """Create a new user account."""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Auth'],
        request=RegisterSerializer,
        responses={201: UserSerializer},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Obtain JWT pair for valid credentials."""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Auth'],
        request=LoginSerializer,
        responses={200: LoginResponseSerializer, 401: OpenApiResponse(description='Invalid credentials')},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        data = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }
        return Response(data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Blacklist refresh token on logout."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Auth'],
        request=LoginResponseSerializer(partial=True),
        responses={205: OpenApiResponse(description='Logged out')},
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'errors': {'refresh': ['This field is required.']}}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({'errors': {'refresh': ['Invalid token.']}}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'Logged out'}, status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    """Return current authenticated user."""

    permission_classes = [IsAuthenticated]

    @extend_schema(tags=['Auth'], responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)
