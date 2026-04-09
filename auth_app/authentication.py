"""Read JWT from httpOnly cookie (SimpleJWT default only uses Authorization header)."""

from django.conf import settings
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate using ``ACCESS_TOKEN_COOKIE``; returns None if cookie absent."""

    def authenticate(self, request: Request):
        raw = request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE)
        if not raw:
            return None
        validated = self.get_validated_token(raw)
        return self.get_user(validated), validated
