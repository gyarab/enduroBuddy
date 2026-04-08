from django.urls import path

from .views.auth import auth_me

urlpatterns = [
    path("auth/me/", auth_me, name="api_auth_me"),
]
