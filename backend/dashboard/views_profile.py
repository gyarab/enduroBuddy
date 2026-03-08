from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse

from accounts.models import CoachAthlete, CoachJoinRequest
from .views_shared import _resolve_coach_from_code


@login_required
def profile_manage(request):
    if request.method != "POST":
        return redirect("dashboard_home")

    action = request.POST.get("action", "")

    if action == "update_profile":
        first_name = (request.POST.get("first_name") or "").strip()[:150]
        last_name = (request.POST.get("last_name") or "").strip()[:150]
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.save(update_fields=["first_name", "last_name"])
        messages.success(request, "Profil byl ulozen.")
        return _redirect_back(request)

    if action == "change_password":
        old_password = request.POST.get("old_password") or ""
        new_password = request.POST.get("new_password") or ""
        new_password_confirm = request.POST.get("new_password_confirm") or ""

        if not request.user.check_password(old_password):
            messages.error(request, "Stare heslo neni spravne.")
            return _redirect_back(request)
        if new_password != new_password_confirm:
            messages.error(request, "Nove heslo a potvrzeni se neshoduji.")
            return _redirect_back(request)

        try:
            validate_password(new_password, user=request.user)
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
            return _redirect_back(request)

        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        update_session_auth_hash(request, request.user)
        messages.success(request, "Heslo bylo zmeneno.")
        return _redirect_back(request)

    if action == "request_coach_by_code":
        coach_code = (request.POST.get("coach_code") or "").strip().upper()
        coach_user = _resolve_coach_from_code(coach_code)
        if coach_user is None:
            messages.error(request, "Kod trenera nebyl nalezen.")
            return _redirect_back(request)
        if coach_user.id == request.user.id:
            messages.error(request, "Nemuzes zadat vlastni kod trenera.")
            return _redirect_back(request)
        if CoachAthlete.objects.filter(coach=coach_user, athlete=request.user).exists():
            messages.info(request, "Uz jsi u tohoto trenera prirazeny.")
            return _redirect_back(request)
        if CoachJoinRequest.objects.filter(
            coach=coach_user,
            athlete=request.user,
            status=CoachJoinRequest.Status.PENDING,
        ).exists():
            messages.info(request, "Pozadavek uz ceka na schvaleni.")
            return _redirect_back(request)
        CoachJoinRequest.objects.create(
            coach=coach_user,
            athlete=request.user,
            status=CoachJoinRequest.Status.PENDING,
        )
        messages.success(request, "Pozadavek byl odeslan trenerovi ke schvaleni.")
        return _redirect_back(request)

    messages.error(request, "Neznamy pozadavek.")
    return _redirect_back(request)


def _redirect_back(request):
    next_url = (request.POST.get("next") or "").strip()
    if next_url:
        return redirect(next_url)
    return redirect(reverse("dashboard_home"))
