from __future__ import annotations

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema

from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UserSerializer,
)


@extend_schema(tags=["Auth"], responses=UserSerializer)
class RegisterView(generics.CreateAPIView):
    """Create a new user account."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):  # type: ignore[override]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Auth"], responses=LoginSerializer)
class LoginView(TokenObtainPairView):
    """Obtain JWT token pair."""

    serializer_class = LoginSerializer


@extend_schema(tags=["Auth"], responses=UserSerializer)
class MeView(generics.RetrieveAPIView):
    """Return the authenticated user's profile."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):  # pragma: no cover - simple property
        return self.request.user


@extend_schema(tags=["Auth"])
class LogoutView(APIView):
    """Blacklist refresh token on logout."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = RefreshToken(serializer.validated_data["refresh"])
        token.blacklist()
        return Response({"detail": "Logged out"}, status=status.HTTP_205_RESET_CONTENT)
