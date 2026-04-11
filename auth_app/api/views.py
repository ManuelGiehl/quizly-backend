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
    return Response({"status": "ok"})


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.create(serializer.validated_data)
    return Response({"detail": "User created successfully!"}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    access, refresh = build_tokens(user)
    response = Response(login_success_payload(user))
    return set_auth_cookies(response, access, refresh)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    return build_logout_response(request)


@api_view(["POST"])
@permission_classes([AllowAny])
def token_refresh(request):
    return build_token_refresh_response(request)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the authenticated user when the JWT cookie (or header) is valid."""
    user = request.user
    return Response(
        {"id": user.id, "username": user.username, "email": user.email},
    )

