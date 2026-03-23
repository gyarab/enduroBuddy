from allauth.account.views import LoginView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie

from accounts.forms import GoogleProfileCompletionForm


@method_decorator(ensure_csrf_cookie, name="dispatch")
class EnduroLoginView(LoginView):
    """Ensure CSRF cookie is always present on GET /accounts/login/."""


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
