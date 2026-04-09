"""JWT cookie helpers for auth endpoints."""

from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def build_tokens(user):
    """Return (access_jwt, refresh_jwt) for the given user."""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def set_auth_cookies(response, access, refresh):
    """Attach httpOnly JWT cookies; tokens are not returned in the JSON body."""
    opts = {
        "httponly": True,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "path": "/",
    }
    response.set_cookie(settings.ACCESS_TOKEN_COOKIE, access, **opts)
    response.set_cookie(settings.REFRESH_TOKEN_COOKIE, refresh, **opts)
    return response


def login_success_payload(user):
    """JSON body shape for successful login (per API contract)."""
    return {
        "detail": "Login successfully!",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
    }
