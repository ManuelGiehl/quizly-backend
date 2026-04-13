"""Auth API views (function-based DRF endpoints).

Keep views small: validation via serializers, JWT cookie work in ``auth_app.services``.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from auth_app.services import (
    build_logout_response,
    build_token_refresh_response,
    build_tokens,
    login_success_payload,
    set_auth_cookies,
)

from .serializers import LoginSerializer, RegisterSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def health(_request):
    """Health-check endpoint used for smoke tests and liveness probes."""
    return Response({"status": "ok"})


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """Create a new user account from the registration payload."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.create(serializer.validated_data)
    return Response({"detail": "User created successfully!"}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Validate credentials and set JWT access/refresh as httpOnly cookies."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    access, refresh = build_tokens(user)
    response = Response(login_success_payload(user))
    return set_auth_cookies(response, access, refresh)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """Clear auth cookies and invalidate refresh token when possible."""
    return build_logout_response(request)


@api_view(["POST"])
@permission_classes([AllowAny])
def token_refresh(request):
    """Issue a new access token based on the refresh cookie."""
    return build_token_refresh_response(request)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the currently authenticated user (cookie JWT or Bearer token)."""
    user = request.user
    return Response(
        {"id": user.id, "username": user.username, "email": user.email},
    )

