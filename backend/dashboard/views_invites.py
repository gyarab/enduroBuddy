from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import CoachAthlete, TrainingGroupAthlete, TrainingGroupInvite
from dashboard.services.month_cards import is_coach
from dashboard.texts import InviteText

@login_required
def accept_training_group_invite(request, token: str):
    invite = (
        TrainingGroupInvite.objects.select_related("group", "group__coach", "used_by")
        .filter(token=token)
        .first()
    )
    if invite is None:
        messages.error(request, InviteText.INVITE_NOT_FOUND)
        return redirect("dashboard_home")

    is_expired = invite.expires_at <= timezone.now()
    is_used = invite.used_at is not None

    if request.method == "POST":
        if is_used:
            messages.error(request, InviteText.INVITE_ALREADY_USED)
            return redirect("dashboard_home")
        if is_expired:
            messages.error(request, InviteText.INVITE_EXPIRED)
            return redirect("dashboard_home")
        if request.user.id == invite.group.coach_id:
            messages.error(request, InviteText.COACH_CANNOT_ACCEPT_OWN_INVITE)
            return redirect("dashboard_home")

        TrainingGroupAthlete.objects.get_or_create(group=invite.group, athlete=request.user)
        CoachAthlete.objects.get_or_create(coach=invite.group.coach, athlete=request.user)
        invite.used_at = timezone.now()
        invite.used_by = request.user
        invite.save(update_fields=["used_at", "used_by"])
        messages.success(request, InviteText.INVITE_ACCEPTED)
        return redirect("dashboard_home")

    return render(
        request,
        "dashboard/accept_training_group_invite.html",
        {
            "invite": invite,
            "is_expired": is_expired,
            "is_used": is_used,
            "is_coach": is_coach(request.user),
        },
    )
