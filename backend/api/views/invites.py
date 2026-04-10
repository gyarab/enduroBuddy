from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from accounts.models import CoachAthlete, TrainingGroupAthlete, TrainingGroupInvite
from dashboard.api import json_error
from dashboard.services.month_cards import display_name, is_coach
from dashboard.texts import InviteText


@login_required
@require_GET
def invite_detail(request, token: str):
    invite = (
        TrainingGroupInvite.objects
        .select_related("group", "group__coach")
        .filter(token=token)
        .first()
    )
    if invite is None:
        return json_error(InviteText.INVITE_NOT_FOUND, status=404)

    return JsonResponse({
        "ok": True,
        "group_name": invite.group.name,
        "coach_name": display_name(invite.group.coach),
        "is_expired": invite.expires_at <= timezone.now(),
        "is_used": invite.used_at is not None,
    })


@login_required
@require_http_methods(["POST"])
def invite_accept(request, token: str):
    invite = (
        TrainingGroupInvite.objects
        .select_related("group", "group__coach")
        .filter(token=token)
        .first()
    )
    if invite is None:
        return json_error(InviteText.INVITE_NOT_FOUND, status=404)

    if invite.used_at is not None:
        return json_error(InviteText.INVITE_ALREADY_USED, status=400)

    if invite.expires_at <= timezone.now():
        return json_error(InviteText.INVITE_EXPIRED, status=400)

    if request.user.id == invite.group.coach_id:
        return json_error(InviteText.COACH_CANNOT_ACCEPT_OWN_INVITE, status=400)

    if is_coach(request.user):
        return json_error("Coaches cannot join training groups as athletes.", status=400)

    TrainingGroupAthlete.objects.get_or_create(group=invite.group, athlete=request.user)
    CoachAthlete.objects.get_or_create(coach=invite.group.coach, athlete=request.user)
    invite.used_at = timezone.now()
    invite.used_by = request.user
    invite.save(update_fields=["used_at", "used_by"])

    return JsonResponse({"ok": True, "message": InviteText.INVITE_ACCEPTED})
