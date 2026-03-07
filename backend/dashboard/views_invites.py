from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import CoachAthlete, TrainingGroupAthlete, TrainingGroupInvite
from dashboard.services.month_cards import is_coach

@login_required
def accept_training_group_invite(request, token: str):
    invite = (
        TrainingGroupInvite.objects.select_related("group", "group__coach", "used_by")
        .filter(token=token)
        .first()
    )
    if invite is None:
        messages.error(request, "Pozv\u00e1nka neexistuje.")
        return redirect("dashboard_home")

    is_expired = invite.expires_at <= timezone.now()
    is_used = invite.used_at is not None

    if request.method == "POST":
        if is_used:
            messages.error(request, "Pozv\u00e1nka u\u017e byla pou\u017eita.")
            return redirect("dashboard_home")
        if is_expired:
            messages.error(request, "Pozv\u00e1nka u\u017e vypr\u0161ela.")
            return redirect("dashboard_home")
        if request.user.id == invite.group.coach_id:
            messages.error(request, "Tren\u00e9r nem\u016f\u017ee p\u0159ijmout vlastn\u00ed pozv\u00e1nku.")
            return redirect("dashboard_home")

        TrainingGroupAthlete.objects.get_or_create(group=invite.group, athlete=request.user)
        CoachAthlete.objects.get_or_create(coach=invite.group.coach, athlete=request.user)
        invite.used_at = timezone.now()
        invite.used_by = request.user
        invite.save(update_fields=["used_at", "used_by"])
        messages.success(request, "Byl/a jsi p\u0159id\u00e1n/a do tr\u00e9ninkov\u00e9 skupiny.")
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
