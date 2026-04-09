from django.urls import path

from . import cookietest, views

urlpatterns = [
    path("health/", views.health, name="auth-health"),
    path("register/", views.register, name="auth-register"),
    path("login/", views.login, name="auth-login"),
    path("me/", cookietest.me, name="auth-me"),
]

