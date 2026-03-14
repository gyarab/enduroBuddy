from __future__ import annotations

import time

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

from accounts.models import CoachAthlete, CoachJoinRequest
from accounts.services.notifications import notify_new_coach_join_request
from dashboard.texts import HomeText, ProfileText
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
        return _profile_response(
            request,
            ok=True,
            message=ProfileText.PROFILE_SAVED,
            tone="success",
            extra={"refresh_profile_modal": True},
        )

    if action == "change_password":
        old_password = request.POST.get("old_password") or ""
        new_password = request.POST.get("new_password") or ""
        new_password_confirm = request.POST.get("new_password_confirm") or ""

        if not request.user.check_password(old_password):
            return _profile_response(request, ok=False, message=ProfileText.OLD_PASSWORD_INVALID, tone="danger", status=400)
        if new_password != new_password_confirm:
            return _profile_response(request, ok=False, message=ProfileText.PASSWORD_CONFIRM_MISMATCH, tone="danger", status=400)

        try:
            validate_password(new_password, user=request.user)
        except ValidationError as exc:
            return _profile_response(request, ok=False, message=" ".join(exc.messages), tone="danger", status=400)

        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        update_session_auth_hash(request, request.user)
        return _profile_response(
            request,
            ok=True,
            message=ProfileText.PASSWORD_CHANGED,
            tone="success",
            extra={"refresh_profile_modal": True},
        )

    if action == "request_coach_by_code":
        if (request.POST.get("test_button_loading") or "").strip() == "add_coach":
            time.sleep(10)

        coach_code = (request.POST.get("coach_code") or "").strip().upper()
        coach_user = _resolve_coach_from_code(coach_code)
        if coach_user is None:
            return _profile_response(request, ok=False, message=HomeText.COACH_CODE_NOT_FOUND, tone="danger", status=400)
        if coach_user.id == request.user.id:
            return _profile_response(request, ok=False, message=HomeText.OWN_COACH_CODE, tone="danger", status=400)
        if CoachAthlete.objects.filter(coach=coach_user, athlete=request.user).exists():
            return _profile_response(request, ok=True, message=HomeText.ALREADY_ASSIGNED_TO_COACH, tone="info")
        if CoachJoinRequest.objects.filter(
            coach=coach_user,
            athlete=request.user,
            status=CoachJoinRequest.Status.PENDING,
        ).exists():
            return _profile_response(request, ok=True, message=HomeText.JOIN_REQUEST_ALREADY_PENDING, tone="info")
        join_request = CoachJoinRequest.objects.create(
            coach=coach_user,
            athlete=request.user,
            status=CoachJoinRequest.Status.PENDING,
        )
        notify_new_coach_join_request(join_request=join_request)
        return _profile_response(
            request,
            ok=True,
            message=HomeText.JOIN_REQUEST_SENT,
            tone="success",
            extra={"refresh_profile_modal": True},
        )

    return _profile_response(request, ok=False, message=ProfileText.UNKNOWN_ACTION, tone="danger", status=400)


def _redirect_back(request):
    next_url = (request.POST.get("next") or "").strip()
    if next_url:
        return redirect(next_url)
    return redirect(reverse("dashboard_home"))


def _is_ajax(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _profile_response(request, *, ok: bool, message: str, tone: str, status: int = 200, extra: dict | None = None):
    if _is_ajax(request):
        payload = {"ok": ok, "message": message, "tone": tone}
        if extra:
            payload.update(extra)
        return JsonResponse(payload, status=status)

    level = {
        "success": "success",
        "danger": "error",
        "warning": "warning",
        "info": "info",
        "secondary": "info",
    }.get(tone, "info")
    getattr(messages, level)(request, message)
    return _redirect_back(request)
