from allauth.account import views as account_views
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from urllib.parse import urlencode

from config.views_nuxt import nuxt_redirect


def _spa_or_public(request, *, requires_auth: bool = False, path: str | None = None):
    return nuxt_redirect(request, path=path or "")


def spa_account_login(request, *args, **kwargs):
    if getattr(request.user, "is_authenticated", False) and not _google_profile_is_complete(request.user):
        return redirect(f"{reverse('account_complete_profile')}?{urlencode({'next': request.get_full_path()})}")
    return _spa_or_public(request, path="accounts/login")


def spa_account_signup(request, *args, **kwargs):
    if request.method == "GET" and not settings.REGISTRATION_ENABLED:
        return redirect(reverse("account_login"))
    return _spa_or_public(request, path="accounts/signup")


def spa_account_logout(request, *args, **kwargs):
    if request.method == "POST":
        return account_views.logout(request, *args, **kwargs)
    return _spa_or_public(request, path="accounts/logout")


def spa_account_password_reset(request, *args, **kwargs):
    return _spa_or_public(request, path="accounts/password/reset")


def spa_account_password_reset_done(request, *args, **kwargs):
    return _spa_or_public(request, path="accounts/password/reset/done")


def spa_account_password_reset_from_key(request, uidb36: str, key: str, *args, **kwargs):
    return _spa_or_public(request, path=f"accounts/password/reset/key/{uidb36}-{key}")


def spa_account_password_reset_from_key_done(request, *args, **kwargs):
    return _spa_or_public(request, path="accounts/password/reset/key/done")


def spa_account_email(request, *args, **kwargs):
    return _spa_or_public(request, requires_auth=True, path="accounts/email")


def spa_account_password_change(request, *args, **kwargs):
    return _spa_or_public(request, requires_auth=True, path="accounts/password/change")


def spa_account_password_set(request, *args, **kwargs):
    return _spa_or_public(request, requires_auth=True, path="accounts/password/set")


def spa_account_reauthenticate(request, *args, **kwargs):
    return _spa_or_public(request, requires_auth=True, path="accounts/reauthenticate")


def spa_account_email_verification_sent(request, *args, **kwargs):
    return _spa_or_public(request, path="accounts/confirm-email")


def spa_account_email_confirm(request, key: str, *args, **kwargs):
    return _spa_or_public(request, path=f"accounts/confirm-email/{key}")


def spa_account_inactive(request, *args, **kwargs):
    return _spa_or_public(request, path="accounts/inactive")


def spa_social_login_error(request, *args, **kwargs):
    return _spa_or_public(request, path="accounts/social/login/error")


def spa_social_login_cancelled(request, *args, **kwargs):
    return _spa_or_public(request, path="accounts/social/login/cancelled")


def spa_social_connections(request, *args, **kwargs):
    return _spa_or_public(request, requires_auth=True, path="accounts/social/connections")


def _safe_next_url(request) -> str:
    candidate = (request.POST.get("next") or request.GET.get("next") or "").strip()
    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return ""


def _google_profile_is_complete(user) -> bool:
    profile = user.profile
    return bool(
        getattr(profile, "google_profile_completed", False)
        and getattr(profile, "google_role_confirmed", False)
    )
