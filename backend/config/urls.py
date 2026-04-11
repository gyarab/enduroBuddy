"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import (
    spa_account_email,
    spa_account_email_confirm,
    spa_account_email_verification_sent,
    spa_account_inactive,
    spa_account_login,
    spa_account_logout,
    spa_account_password_change,
    spa_account_password_reset,
    spa_account_password_reset_from_key,
    spa_account_password_reset_from_key_done,
    spa_account_password_reset_done,
    spa_account_password_set,
    spa_account_reauthenticate,
    spa_account_signup,
    spa_social_connections,
    spa_social_login_cancelled,
    spa_social_login_error,
)
from config import error_views
from config.views_public import public_about, public_home, public_privacy, public_terms
from config.views_spa import public_spa_entry, spa_entry

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/v1/", include("api.urls")),
    path("accounts/login/", spa_account_login, name="account_login"),
    path("accounts/signup/", spa_account_signup, name="account_signup"),
    path("accounts/logout/", spa_account_logout, name="account_logout"),
    path("accounts/inactive/", spa_account_inactive, name="account_inactive"),
    path("accounts/email/", spa_account_email, name="account_email"),
    path("accounts/confirm-email/", spa_account_email_verification_sent, name="account_email_verification_sent"),
    re_path(r"^accounts/confirm-email/(?P<key>[-:\w]+)/$", spa_account_email_confirm, name="account_confirm_email"),
    path("accounts/password/change/", spa_account_password_change, name="account_change_password"),
    path("accounts/password/set/", spa_account_password_set, name="account_set_password"),
    path("accounts/reauthenticate/", spa_account_reauthenticate, name="account_reauthenticate"),
    path("accounts/password/reset/", spa_account_password_reset, name="account_reset_password"),
    path("accounts/password/reset/done/", spa_account_password_reset_done, name="account_reset_password_done"),
    re_path(
        r"^accounts/password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        spa_account_password_reset_from_key,
        name="account_reset_password_from_key",
    ),
    path("accounts/password/reset/key/done/", spa_account_password_reset_from_key_done, name="account_reset_password_from_key_done"),
    path("accounts/social/login/error/", spa_social_login_error, name="socialaccount_login_error"),
    path("accounts/social/login/cancelled/", spa_social_login_cancelled, name="socialaccount_login_cancelled"),
    path("accounts/social/connections/", spa_social_connections, name="socialaccount_connections"),
    path("app/profile/complete", spa_entry, name="account_complete_profile"),
    path("accounts/", include("allauth.urls")),
    path("__debug/ui/errors/", error_views.error_preview_index, name="error_preview_index"),
    path("__debug/ui/errors/<int:status_code>/", error_views.error_preview_status, name="error_preview_status"),
    path("", public_home, name="public_home"),
    path("about/", public_about, name="public_about"),
    path("terms/", public_terms, name="public_terms"),
    path("privacy/", public_privacy, name="public_privacy"),
    path("auth-preview/", public_spa_entry, name="spa_auth_preview_root"),
    re_path(r"^auth-preview/(?P<path>.*)$", public_spa_entry, name="spa_auth_preview"),
    path("app/", spa_entry, name="spa_app_root"),
    re_path(r"^app/(?P<path>.*)$", spa_entry, name="spa_app"),
    path("coach/", spa_entry, name="spa_coach_root"),
    re_path(r"^coach/(?P<path>.*)$", spa_entry, name="spa_coach"),
    path("", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = "config.error_views.bad_request"
handler403 = "config.error_views.permission_denied"
handler404 = "config.error_views.page_not_found"
handler500 = "config.error_views.server_error"

