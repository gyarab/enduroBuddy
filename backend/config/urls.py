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
    path("accounts/", include("allauth.urls")),
    path("__debug/ui/errors/", error_views.error_preview_index, name="error_preview_index"),
    path("__debug/ui/errors/<int:status_code>/", error_views.error_preview_status, name="error_preview_status"),
    path("", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = "config.error_views.bad_request"
handler403 = "config.error_views.permission_denied"
handler404 = "config.error_views.page_not_found"
handler500 = "config.error_views.server_error"

