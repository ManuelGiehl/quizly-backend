"""Read JWT from httpOnly cookie (SimpleJWT default only uses Authorization header)."""

from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticate using ``ACCESS_TOKEN_COOKIE``; returns None if cookie absent.

    Invalid or expired cookies must not raise: otherwise ``POST /api/login/``
    fails while the browser still sends an old ``access_token`` (AllowAny).
    """

    def authenticate(self, request: Request):
        raw = request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE)
        if not raw:
            return None
        try:
            validated = self.get_validated_token(raw)
        except (InvalidToken, TokenError):
            return None
        try:
            return self.get_user(validated), validated
        except AuthenticationFailed:
            return None
