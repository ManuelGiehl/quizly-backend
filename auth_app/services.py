"""JWT cookie helpers for auth endpoints."""

from django.conf import settings
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

LOGOUT_SUCCESS_DETAIL = (
    "Log-Out successfully! All Tokens will be deleted. "
    "Refresh token is now invalid."
)


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


def clear_auth_cookies(response):
    """Remove JWT cookies from the client (httpOnly cookies must be cleared server-side)."""
    response.delete_cookie(settings.ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(settings.REFRESH_TOKEN_COOKIE, path="/")
    return response


def blacklist_refresh_if_present(refresh_token):
    """Invalidate refresh JWT in the blacklist table; ignore invalid/expired tokens."""
    if not refresh_token:
        return
    try:
        RefreshToken(refresh_token).blacklist()
    except TokenError:
        pass


def build_logout_response(request):
    """200 response: blacklist refresh cookie, clear cookies, exact API detail string."""
    refresh = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE)
    blacklist_refresh_if_present(refresh)
    response = Response({"detail": LOGOUT_SUCCESS_DETAIL})
    return clear_auth_cookies(response)
