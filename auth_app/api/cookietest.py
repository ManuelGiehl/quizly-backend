"""
Manual / Postman helper: verifies that the httpOnly ``access_token`` cookie
is accepted by ``CookieJWTAuthentication``.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the authenticated user when the JWT cookie is valid."""
    user = request.user
    return Response(
        {"id": user.id, "username": user.username, "email": user.email},
    )
