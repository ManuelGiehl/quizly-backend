"""Auth API routes (health, register, login, token refresh, me)."""

from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health, name="auth-health"),
    path("register/", views.register, name="auth-register"),
    path("login/", views.login, name="auth-login"),
    path("logout/", views.logout, name="auth-logout"),
    path("token/refresh/", views.token_refresh, name="auth-token-refresh"),
    path("me/", views.me, name="auth-me"),
]

