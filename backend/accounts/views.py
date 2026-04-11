from allauth.account import views as account_views
from allauth.account.views import LoginView
from allauth.socialaccount import views as socialaccount_views
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from urllib.parse import urlencode

from accounts.forms import GoogleProfileCompletionForm
from config.views_spa import public_spa_entry, spa_entry


@method_decorator(ensure_csrf_cookie, name="dispatch")
class EnduroLoginView(LoginView):
    """Ensure CSRF cookie is always present on GET /accounts/login/."""


def _spa_or_public(request, *, requires_auth: bool = False, path: str | None = None):
    if requires_auth:
        return spa_entry(request, path=path)
    return public_spa_entry(request, path=path)


def spa_account_login(request, *args, **kwargs):
    if request.method == "GET":
        if getattr(request.user, "is_authenticated", False) and not _google_profile_is_complete(request.user):
            return redirect(f"{reverse('account_complete_profile')}?{urlencode({'next': request.get_full_path()})}")
        return _spa_or_public(request, path="accounts/login")
    return EnduroLoginView.as_view()(request, *args, **kwargs)


def spa_account_signup(request, *args, **kwargs):
    if request.method == "GET":
        return _spa_or_public(request, path="accounts/signup")
    return account_views.signup(request, *args, **kwargs)


def spa_account_logout(request, *args, **kwargs):
    if request.method == "GET":
        return _spa_or_public(request, path="accounts/logout")
    return account_views.logout(request, *args, **kwargs)


def spa_account_password_reset(request, *args, **kwargs):
    if request.method == "GET":
        return _spa_or_public(request, path="accounts/password/reset")
    return account_views.password_reset(request, *args, **kwargs)


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
    if request.method == "GET":
        return _spa_or_public(request, requires_auth=True, path="accounts/social/connections")
    return socialaccount_views.connections(request, *args, **kwargs)


@login_required
def complete_profile(request):
    next_url = _safe_next_url(request)
    if _google_profile_is_complete(request.user):
        return redirect(next_url or reverse("dashboard_home"))

    if request.method == "POST":
        form = GoogleProfileCompletionForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            request.user.profile.google_profile_completed = True
            request.user.profile.google_role_confirmed = True
            request.user.profile.save(update_fields=["google_profile_completed", "google_role_confirmed"])
            messages.success(request, "Profil byl doplněn.")
            return redirect(next_url or reverse("dashboard_home"))
    else:
        form = GoogleProfileCompletionForm(user=request.user)

    return render(
        request,
        "account/complete_profile.html",
        {
            "form": form,
            "next_url": next_url or reverse("dashboard_home"),
        },
    )


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
