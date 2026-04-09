from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from accounts.forms import GoogleProfileCompletionForm
from accounts.models import Role
from dashboard.api import json_error
from dashboard.texts import ProfileText


def _safe_next_url(request) -> str:
    candidate = ""
    if request.method == "GET":
        candidate = (request.GET.get("next") or "").strip()
    else:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return ""
        candidate = (payload.get("next") or "").strip() if isinstance(payload, dict) else ""

    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return ""


@login_required
@require_http_methods(["GET", "PATCH"])
def profile_completion(request):
    profile = request.user.profile

    if request.method == "GET":
        return JsonResponse(
            {
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "role": getattr(profile, "role", Role.ATHLETE),
                "role_options": [
                    {"value": Role.COACH, "label": "Trener"},
                    {"value": Role.ATHLETE, "label": "Sverenec"},
                ],
                "google_profile_completed": bool(getattr(profile, "google_profile_completed", False)),
                "google_role_confirmed": bool(getattr(profile, "google_role_confirmed", False)),
                "next": _safe_next_url(request),
            }
        )

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return json_error(ProfileText.UNKNOWN_ACTION, status=400)

    if not isinstance(payload, dict):
        return json_error(ProfileText.UNKNOWN_ACTION, status=400)

    form = GoogleProfileCompletionForm(
        {
            "first_name": payload.get("first_name", ""),
            "last_name": payload.get("last_name", ""),
            "role": payload.get("role", Role.ATHLETE),
        },
        user=request.user,
    )
    if not form.is_valid():
        return JsonResponse(
            {
                "ok": False,
                "message": "Oprav prosim oznacena pole.",
                "errors": {field: [str(error) for error in errors] for field, errors in form.errors.items()},
            },
            status=400,
        )

    form.save()
    profile.google_profile_completed = True
    profile.google_role_confirmed = True
    profile.save(update_fields=["google_profile_completed", "google_role_confirmed"])

    role = getattr(profile, "role", Role.ATHLETE)
    redirect_to = _safe_next_url(request) or ("/coach/plans" if role == Role.COACH else "/app/dashboard")
    return JsonResponse(
        {
            "ok": True,
            "message": "Profil byl doplnen.",
            "redirect_to": redirect_to,
            "profile": {
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "role": role,
                "google_profile_completed": True,
                "google_role_confirmed": True,
            },
        }
    )
